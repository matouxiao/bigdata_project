import requests
from bs4 import BeautifulSoup
import time
import csv  # 导入 csv 模块
import datetime  # 导入日期处理模块
import re  # 导入正则表达式模块

# 日期处理函数
def parse_date_from_update_time(update_time):
    """从更新时间字符串中提取日期部分"""
    today = datetime.datetime.now().date()
    
    # 输出原始时间字符串供调试
    print(f"解析时间字符串: '{update_time}'")
    
    # 处理常见格式: "04-14 10:56"
    match = re.search(r'(\d{2}-\d{2})\s+\d{2}:\d{2}', update_time)
    if match:
        month_day = match.group(1)
        return f"{today.year}-{month_day}"
    
    # 处理"今天 xx:xx"格式
    if '今天' in update_time:
        return today.strftime('%Y-%m-%d')
    
    # 处理"昨天 xx:xx"格式
    if '昨天' in update_time:
        yesterday = today - datetime.timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d')
    
    # 处理完整日期格式 "xxxx-xx-xx"
    if len(update_time) >= 10 and update_time[4] == '-' and update_time[7] == '-':
        return update_time[:10]
    
    # 其他情况
    print(f"警告：无法识别的时间格式: '{update_time}'，使用今天日期")
    return today.strftime('%Y-%m-%d')

def convert_str_to_date(date_str):
    """将日期字符串转换为日期对象"""
    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        print(f"无法解析日期: {date_str}，使用今天日期代替")
        return datetime.datetime.now().date()

# 函数重命名以反映其功能扩展
def get_guba_posts(stock_code, pages=5, max_posts=1000, min_date_span_days=30, max_posts_per_day=30):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        # 更新Cookie
        'Cookie': 'qgqp_b_id=df383e2e5c48718dd10c621d5fa4aa39; st_si=43831360160588; st_asi=delete; st_pvi=13788631049269; st_sp=2025-04-14%2010%3A16%3A57; st_inirUrl=https%3A%2F%2Fguba.eastmoney.com%2Frank%2F; st_sn=19; st_psi=' + str(int(time.time()*1000)) + '-117001356556-' + str(int(time.time())%10000000000),
        'Referer': 'https://guba.eastmoney.com/'
    }
    
    all_posts_data = []
    posts_count_by_date = {}
    earliest_date = None
    latest_date = None
    date_span_achieved = False
    
    for page in range(1, pages+1):
        url = f'https://guba.eastmoney.com/list,{stock_code}_{page}.html'
        
        try:
            print(f"\n尝试访问页面: {url}")
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            # 检查响应状态
            print(f"页面响应状态: {response.status_code}")
            
            # 保存页面源码以便检查（可选）
            with open(f"debug_page_{stock_code}_{page}.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"已保存页面源码到 debug_page_{stock_code}_{page}.html")
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 查找包含帖子信息的 tr 标签
            post_rows = soup.select('tbody.listbody tr.listitem')
            print(f"找到 {len(post_rows)} 个帖子行")
            
            page_posts = []
            if post_rows:
                for row in post_rows:
                    read_tag = row.select_one('div.read')
                    title_tag = row.select_one('div.title a')
                    update_tag = row.select_one('div.update')
                    
                    # 输出原始HTML结构供检查
                    if update_tag:
                        print(f"原始更新时间HTML: {update_tag}")
                    else:
                        print(f"未找到更新时间标签")
                    
                    # 确保所有需要的标签都存在，并且标题链接是有效的帖子链接
                    if read_tag and title_tag and update_tag and title_tag.has_attr('href') and title_tag['href'].startswith('/news,'):
                        read_count = read_tag.get_text(strip=True)
                        title = title_tag.get_text(strip=True)
                        update_time = update_tag.get_text(strip=True)
                        
                        print(f"原始更新时间: '{update_time}'")
                        
                        # 解析日期
                        date_str = parse_date_from_update_time(update_time)
                        print(f"解析后的日期: '{date_str}'")
                        
                        # 检查该日期的帖子数量是否已达到每日限制
                        if date_str in posts_count_by_date and posts_count_by_date[date_str] >= max_posts_per_day:
                            print(f"日期 {date_str} 的帖子已达到每日限制 {max_posts_per_day} 条，跳过")
                            continue
                        
                        # 更新该日期的帖子计数
                        posts_count_by_date[date_str] = posts_count_by_date.get(date_str, 0) + 1
                        
                        # 添加日期信息到帖子数据
                        post_data = {'read_count': read_count, 'title': title, 'update_time': update_time, 'date': date_str}
                        page_posts.append(post_data)
                        
                        # 更新日期范围
                        current_date = convert_str_to_date(date_str)
                        if earliest_date is None or current_date < earliest_date:
                            earliest_date = current_date
                        if latest_date is None or current_date > latest_date:
                            latest_date = current_date
                        
                        # 检查日期跨度是否已达到要求
                        if earliest_date and latest_date:
                            date_span = (latest_date - earliest_date).days
                            if date_span >= min_date_span_days and not date_span_achieved:
                                date_span_achieved = True
                                print(f"已达到最小日期跨度要求: {date_span} 天 (要求 {min_date_span_days} 天)")
            
            # 如果主要选择器未找到数据，可以尝试备用选择器（如果网站结构有多种可能）
            # 注意：备用选择器逻辑需要根据实际情况调整，这里仅作示例保留
            if not page_posts:
                 # 尝试查找另一种可能的结构，例如针对置顶帖或不同类型的帖子
                 # 注意：这里的备用选择器 'div.articleh.normal_post' 看起来不像是行选择器，需要根据实际HTML调整
                 alternative_rows = soup.select('div.articleh.normal_post') # 示例，需要根据实际HTML调整
                 if alternative_rows:
                     print(f'第 {page} 页尝试备用选择器...')
                     # 此处需要添加从 alternative_rows 提取数据的逻辑
                     # ... (根据 alternative_rows 的结构编写提取代码) ...
                     pass # 占位符

                 if not page_posts: # 如果备用逻辑也没有提取到数据
                    print(f'第 {page} 页未找到帖子数据，可能已到达末页或页面结构已更改。')
                    break

            all_posts_data.extend(page_posts)
            print(f'已爬取第 {page} 页，找到 {len(page_posts)} 条帖子数据，当前总计: {len(all_posts_data)} 条')
            
            # 检查是否达到总帖子数量限制
            if len(all_posts_data) >= max_posts:
                print(f'已达到最大帖子数量限制 ({max_posts} 条)，停止爬取')
                all_posts_data = all_posts_data[:max_posts]  # 截断至最大限制
                break
            
            time.sleep(1.5 + time.time() % 1)
            
        except requests.exceptions.RequestException as e:
            print(f'请求第 {page} 页时出错: {str(e)}')
            break
        except Exception as e:
            print(f'处理第 {page} 页时出错: {str(e)}')
            import traceback
            print(traceback.format_exc())  # 打印详细错误堆栈
            break
    
    # 输出日期跨度信息
    if earliest_date and latest_date:
        date_span = (latest_date - earliest_date).days
        print(f'爬取完成，日期跨度: {date_span} 天 (从 {earliest_date} 到 {latest_date})')
    
    # 处理返回前去除临时添加的日期字段
    for post in all_posts_data:
        if 'date' in post:
            del post['date']
            
    return all_posts_data

# 使用示例
if __name__ == '__main__':
    # 添加日期测试
    test_dates = [
        "04-14 10:56",
        "05-07 15:30", 
        "今天 09:45",
        "昨天 22:15",
        "2025-05-07 16:30",
        "置顶"  # 测试异常情况
    ]
    
    print("===测试日期解析===")
    for test_date in test_dates:
        parsed = parse_date_from_update_time(test_date)
        print(f"原始: '{test_date}' -> 解析: '{parsed}'")
    print("===测试结束===\n")
    
    # 使用单个股票代码进行调试
    stock_codes = ['000524']  # 仅测试一个股票代码

    for stock_code in stock_codes:
        print(f"\n--- 开始爬取股票代码: {stock_code} ---")
        # 调用更新后的函数，添加参数控制
        posts_data = get_guba_posts(
            stock_code, 
            pages=20,  # 增加页数以确保可以爬取足够的数据
            max_posts=1000,  # 最多爬取1000条
            min_date_span_days=50,  # 最小日期跨度为30天
            max_posts_per_day=30  # 每天最多爬取30条
        ) 
        if posts_data:
            print(f'\n--- 股票代码 {stock_code} 爬取到的数据 ---')
            for i, post in enumerate(posts_data[:5], 1): # 打印前5条
                print(f"{i}. 阅读: {post['read_count']}, 标题: {post['title']}, 时间: {post['update_time']}")
            print(f'--- 共爬取 {len(posts_data)} 条帖子数据 ---')

            # 保存数据到 CSV 文件
            file_name = f'{stock_code}_posts_data.csv' # 更新文件名
            try:
                with open(file_name, 'w', newline='', encoding='utf-8-sig') as f:
                    # 定义表头
                    fieldnames = ['read_count', 'title', 'update_time']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    
                    writer.writeheader()  # 写入表头
                    writer.writerows(posts_data) # 写入数据行
                print(f'数据已保存到 {file_name}')
            except IOError as e:
                print(f"写入文件 {file_name} 时出错: {e}")
            except Exception as e:
                 print(f"处理文件 {file_name} 时发生未知错误: {e}")

        else:
            print(f'\n未能为股票代码 {stock_code} 爬取到任何帖子数据。')

        time.sleep(2 + time.time() % 1)

    print("\n--- 所有股票代码处理完毕 ---")