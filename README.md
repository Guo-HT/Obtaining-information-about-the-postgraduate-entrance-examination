# Obtaining-information-about-the-postgraduate-entrance-examination
从研招网爬取用户输入的专业代码所对应的院校、研究方向及部分考试科目

#### 介绍
-  从中国研究生信息网中获取硕士研究生招生考试爬取用户输入专业对应的所有开设院校、各院校开设所有研究方向及各方向的部分考试范围（如：数学、专业课）。

#### 软件架构
通过python语言，主要通过requests模块及lxml模块进行数据获取及定位，xlwt模块进行.xls文件的写操作。


#### 安装说明

1.  pip install requests
2.  pip install lxml
3.  pip install xlwt

#### 使用说明

1.  通过浏览器，手动进入研招网硕士专业目录，url：https://yz.chsi.com.cn/zsml/queryAction.do
2.  从学科类别选项中找到专业名称及对应专业代码（如：“软件工程” 对应 0835）
3.  运行代码，根据提示输入专业代码、将要保存的文件名称并选择存储文件类型
4.  从同级目录中打开对应文件

