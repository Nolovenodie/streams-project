# Streams Project

> 云任务视频多码率切片，预览视频，预览图表生成，自动上传结果，HLS 播放器

## 安装环境

-   下载 FFmpeg: https://ffmpeg.org/download.html

## 安装环境

    pip install -r requirements.txt
    npm install -g pkg
    npm install
    curl https://rclone.org/install.sh | sudo bash

## 编译依赖

    # 编译预览表合成程序
    pkg thumbs.js

    # 更改 thumbs 名称
    # Windows: 更改 thumbs-win.exe 名为 thumbs.exe
    mv thumbs-linux thumbs

    # 赋权
    chmod 777 thumbs

## 部署方法

**请修改 sample.env 内 配置 后再部署**

    # 应用配置
    cp sample.env .env

    # 部署云任务 Worker
    # Windows: 因 Celery 不兼容, 如需测试请加上 -P eventlet 后再运行
    celery -A app worker -l error

## 投递任务

    from worker import handle_movie
    print(handle_movie.delay("输入目录", "输出目录").id)

---

## 基于项目

- [python-ffmpeg-video-streaming](https://github.com/hadronepoch/python-ffmpeg-video-streaming)
