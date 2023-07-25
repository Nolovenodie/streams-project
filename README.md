# Streams Project

> 视频多码率切片，预览图表生成，HLS 播放器

## 安装环境

-   前往 FFmpeg 官网下载主程序: https://ffmpeg.org/
-   下载你环境的 Releases

## 使用方法

> 如下命令执行后结果将会存放在视频目录下 视频同名文件夹内

**视频转码切片**

    ./streams 视频路径

**预览图表生成**

    ./thumbs 视频路径

    # 更多参数使用帮助查看
    # ./thumbs --help

## 编译打包

    # 安装编译环境
    pip install -r requirements.txt
    npm install

    # 编译切片程序
    nuitka --standalone --onefile streams.py

    # 编译预览程序
    pkg thumbs.js
