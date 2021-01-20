import requests
from lxml import etree
import time
import re
import xlwt


class Yanzhao(object):
    def __init__(self, num, file='研究生招考信息', _file_type='1'):
        """
        构造基本信息
        :param num: 学科代码
        :param file: 将要存储的文件名
        :param _file_type: 文件的类型：1--.xls  2--.tsv
        """
        self.url_root = 'https://yz.chsi.com.cn/'
        self.url_entrance = 'https://yz.chsi.com.cn/zsml/queryAction.do'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36 Edg/87.0.664.75'
        }
        self.sub_num = num
        self.file_name = file
        self.workbook = xlwt.Workbook()
        self.worksheet = self.workbook.add_sheet('content')
        self.file_type = _file_type

    def get_page(self):
        """
        获取在研招网中该学科开设院校的页数
        :return: 页数
        """
        # 构造请求数据，可变数据：学科、页数
        data = {'ssdm': '', 'dwmc': '', 'mldm': '', 'mlmc': '', 'yjxkdm': self.sub_num, 'zymc': '', 'xxfs': '1',
                'pageno': 1, }
        # 请求
        page_response = requests.post(self.url_entrance, data=data, headers=self.headers)
        page_response_content = page_response.content.decode()
        # 获取页数
        page_content_obj = etree.HTML(page_response_content)
        try:
            page_obj_list = page_content_obj.xpath('//div[@class="zsml-page-box"]//li[last()-1]')
            page_list = page_obj_list[0].xpath('.//text()')
            page = int(page_list[0])
        except:
            page_obj_list = page_content_obj.xpath('//div[@class="zsml-page-box"]//li[last()-2]')
            page_list = page_obj_list[0].xpath('.//text()')
            page = int(page_list[0])
        print('总页数：', page)
        return page

    def get_parse_each_page(self, i):
        """
        从第i页中获取学校对象列表
        :param i: 第几页
        :return: 从每页中获取学校对象列表
        """
        data = {'ssdm': '', 'dwmc': '', 'mldm': '', 'mlmc': '', 'yjxkdm': self.sub_num, 'zymc': '', 'xxfs': '1',
                'pageno': i + 1, }
        response = requests.post('https://yz.chsi.com.cn/zsml/queryAction.do', data=data, headers=self.headers)
        response_content = response.content.decode()
        # 获取对应专业的信息
        content_obj = etree.HTML(response_content)
        # 解析出每页中的所有学校列表
        schools_obj = content_obj.xpath('//table[@class="ch-table"]/tbody/tr')
        return schools_obj

    def parse_school_info(self, school_obj, school_line, school_line_str):
        """
        解析学校基本信息
        :param school_obj: 某个学校对象
        :param school_line: 某个学校信息列表
        :param school_line_str: 某个学校信息字符串，字段间以“\t”隔开
        :return: 学校信息列表，当前学校对应研招网中url， 学校信息字符串
        """
        # 解析一个学校各个信息
        school_td_list = school_obj.xpath('./td')
        # 获取学校的基本信息，名称，链接，地点
        school_url = str()
        # 遍历学校信息
        for td in school_td_list:
            if school_td_list.index(td) == 0:
                school_name = td.xpath('.//a/text()')[0]  # 学校名称
                school_url = td.xpath('.//a/@href')[0]  # 学校链接
                school_url = self.url_root + school_url
                school_line.append(school_name)
                school_line.append(school_url)

                school_line_str = school_name + '\t' + school_url + '\t'  # 字符串连接
            if school_td_list.index(td) == 1:
                school_location = td.xpath('.//text()')[0]  # 学校地点
                school_line.append(school_location)
                school_line.append('-')
                school_line_str += school_location
                school_line_str += '\t-\t'  # 字符串连接
                # 获取地点后直接退出循环
                break
        return school_line, school_url, school_line_str

    def get_school_dir(self, school_url):
        """
        通过学校对应研招网中url，解析出开设方向对象列表
        :param school_url: 某学校对应研招网中url
        :return: 开设方向对象列表
        """
        # 请求学校主页
        school_response = requests.get(school_url, headers=self.headers)
        school_content = school_response.content.decode()
        school_detail = etree.HTML(school_content)
        # 提取学校研究方向
        exam_info_list = school_detail.xpath('//table[@class="ch-table"]/tbody/tr')
        return exam_info_list

    def parse_each_dir(self, each_exam, school_line, school_line_str):
        """
        解析各研究方向的信息，并将对应信息存入信息列表及信息字符串。
        :param each_exam: 研究方向
        :param school_line: 学校信息列表
        :param school_line_str: 学校信息字符串
        :return: 当前研究方向对应考试信息url，学校信息列表及字符串
        """
        # 开设院系
        each_exam_department = each_exam.xpath('./td[2]/text()')[0]
        # 研究方向
        each_exam_dir = each_exam.xpath('./td[4]/text()')[0]
        # 考试范围链接
        exam_info_url_obj = each_exam.xpath('./td[8]/a/@href')
        exam_info_url = exam_info_url_obj[0]
        exam_info_url = self.url_root + exam_info_url  # 构造完整url

        # 学校行信息叠加
        school_line.append(each_exam_department)
        school_line.append(each_exam_dir)
        school_line.append(exam_info_url)
        school_line_str += (each_exam_department + '\t' + each_exam_dir + '\t' + exam_info_url + '\t')
        return exam_info_url, school_line, school_line_str

    def get_exam(self, exam_info_url, school_line, school_line_str):
        """
        获取考试信息
        :param exam_info_url: 考试科目详情对应url
        :param school_line: 学校信息列表
        :param school_line_str: 学校信息字符串
        :return: 学校信息列表、字符串
        """
        # 请求
        each_dir_content_html = requests.get(exam_info_url, headers=self.headers).content.decode()
        # 转变成可解析对象
        exam_obj = etree.HTML(each_dir_content_html)

        # 得到数学和专业课的科目列表
        exam_obj_math = exam_obj.xpath('''//table/tbody[@class='zsml-res-items']/tr/td[3]/text()''')
        exam_obj_pro = exam_obj.xpath('''//table/tbody[@class='zsml-res-items']/tr/td[4]/text()''')

        # 将考试科目列表转变成一个字符串
        exam_math = ''.join(exam_obj_math)
        exam_pro = ''.join(exam_obj_pro)
        # 清除字符串中的换行符
        exam_math = re.sub('\r\n[ ]*', '', exam_math)
        exam_pro = re.sub('\r\n[ ]*', '', exam_pro)

        exam = exam_math + exam_pro
        # 加入学校行信息
        school_line.append(exam)
        school_line.append('-')
        school_line_str += (exam_math + exam_pro + '\t-\t')
        return school_line, school_line_str

    def save_school_line(self, school_line, row_num, school_line_str):
        """
        保存所有信息
        :param school_line: 学校信息列表
        :param row_num: 当前学校所在行数
        :param school_line_str: 学校信息字符串
        :return: None
        """
        if self.file_type == '1':
            for i in range(len(school_line)):
                # print(row_num, i, school_line[i])
                self.worksheet.write(row_num, i, school_line[i])
            self.workbook.save(self.file_name + '.xls')
        elif self.file_type == '2':
            # 写tsv文件
            with open(self.file_name + '.tsv', 'a', encoding='utf-8') as f:
                f.write(school_line_str)

    def run(self):
        """
        类内逻辑主线函数。
        :return: None
        """
        page = self.get_page()
        num = 0
        for i in range(page):
            schools_obj = self.get_parse_each_page(i)  # 得到每页的学校信息
            print('当前页：', len(schools_obj), '所高校')
            # 遍历专业对应的学校
            for school_obj in schools_obj:
                # 此循环内是单个学校
                school_line_list = list()
                school_line_str = str()
                school_line_list, school_url, school_line_str = self.parse_school_info(school_obj, school_line_list,
                                                                                       school_line_str)
                time.sleep(0.1)
                # 请求学校开设专业详情页
                exam_info_list = self.get_school_dir(school_url)
                # 遍历每一个研究方向
                for each_exam in exam_info_list:
                    # 此循环内是每一个研究方向
                    exam_info_url, school_line_list, school_line_str = self.parse_each_dir(each_exam, school_line_list,
                                                                                           school_line_str)
                    time.sleep(0.1)
                    # 请求每个研究方向的主页，提取考试科目
                    school_line_list, school_line_str = self.get_exam(exam_info_url, school_line_list, school_line_str)
                school_line_str += '\n'
                print(school_line_list[0], " done")
                # print(school_line_str)

                self.save_school_line(school_line_list, num, school_line_str)
                num += 1


if __name__ == '__main__':
    print('************************************************************')
    print('**                                                        **')
    print('**                由 Guo Hanting 制作                     **')
    print('**                                                        **')
    print('************************************************************')
    print()
    print('从研招网找到学科类别编号，程序会将该专业所有开设高校及各个方向写入指定文件中，并保存到程序同级目录下\n')
    print('.xls文件直接用Office Excel打开')
    print('.tsv文件用记事本打开 或 拖入excel内打开\n')
    sub_num = input('输入学科类别编号(来自研招网)：')
    file_name = input('输入将保存的文件名：')
    while True:
        file_type = input('选择要保存的文件类型：1->.xls（excel文件）  2->.tsv（记事本表格）')
        if file_type == '1' or file_type == '2':
            break
    yz = Yanzhao(sub_num, file_name, file_type)
    try:
        yz.run()
    except Exception as e:
        print('出现错误：')
        print(e)
    input('\n\n文件以保存在当前文件夹中!!!\n\n按任意键退出')

