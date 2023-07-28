# Streams Project

> 云任务视频多码率切片，预览视频，预览图表生成，自动上传结果，HLS 播放器

## 安装环境

-   下载 FFmpeg: https://ffmpeg.org/download.html
-   下载 Rclone: https://rclone.org/downloads/

## 安装环境

    pip install -r requirements.txt
    npm install -g pkg
    npm install

## 编译依赖

    # 编译预览程序
    pkg thumbs.js

    # 更改 thumbs 名称
    mv thumbs-win.exe thumbs.exe
    mv thumbs-linux thumbs

## 使用方法

**请修改 app.py 内 Redis 地址后再部署**

    # 部署云任务 Worker
    # Windows因Celery原因不适用, 如需测试请加上 -P eventlet 后再运行
    celery -A app worker -l error

投递任务的实例在 main.py
