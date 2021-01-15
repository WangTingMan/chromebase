# Welcome to use chrome base with visual studio
## Tag: libchrome linbase chromebase
This repo is to build the base folder which located in chromium with visual studio on windows.
You can find some usable components from this project, and you can use these component in your
project( but you must comply with the rule from google.

# How to use
1. Download this source code and open chromebase.sln with visual studio 2019.
2. You must use 2019 because that version can offer you the c++17.
3. Generate the first project: libChromeBase
4. Generate the example project: SimpleStackTraceExample
5. Run SimpleStackTraceExample, congratulations! you can start to use this repo right now!
# About the latest chromium version
Actually I do not have much time to keep updating this repo to the latest chromium, but I will try
to update it.


# 剪切chromium的基础库，并且在VS2019中编译
这份源码都来自于chromium项目，这个伟大的项目提供了chrome浏览器、chrome OS并且在安卓8.0以上的系统中的组件：
libchrome。该项目是跨平台的：因为chrome浏览器本身就是跨平台的。那么其中的base库也就是跨平台的了。这里剪切了
其中的base库，并且作为基础组件供大家使用。使用需要遵守google的chromium的许可。提供的组件有（仅列出部分）：
线程池、任务调度、定时器、文件系统、文件操作、日志、base64、OS系统信息、时间库、调试库、json、进程通信等等。
# 如何使用
1. 下载源码，使用VS2019打开sln解决方案文件
2. 编译libChromeBase
3. 编译SimpleStackTraceExample
4. 运行示例程序SimpleStackTraceExample
# 关于更新到chromium最新版
该库是业余时间剪切的，我没有太多时间来更新到最新版，不过有时间的话，我会尽量更新到最新版。
如果有任何使用问题可以提出。
