const ffmpeg = require("fluent-ffmpeg");
const fs = require("fs");
const path = require("path");
const yargs = require("yargs/yargs");
const { hideBin } = require("yargs/helpers");

const argv = yargs(hideBin(process.argv))
	.command("$0 <input>", "主命令", (yargs) => {
		yargs.positional("input", {
			describe: "视频文件",
			type: "string",
		});
	})
	.option("second", {
		alias: "s",
		description: "间隔秒数",
		type: "number",
		default: 10,
	})
	.option("h265", {
		alias: "h265",
		description: "是否为 h265",
		type: "boolean",
		default: false,
	})
	.help().argv;

const inputVideo = argv.input;
const second = argv.second;

const videoName = path.basename(inputVideo, path.extname(inputVideo));
const outputFolder = path.join(path.dirname(inputVideo), videoName);

const streamsDir = path.join(outputFolder, "streams");
if (!fs.existsSync(streamsDir)) {
	fs.mkdirSync(streamsDir, { recursive: true });
}

const m3u8File = path.join(outputFolder, "streams.m3u8");

ffmpeg(inputVideo)
	.addOption("-codec", "copy")
	.addOption("-bsf:v", argv.h265 ? "hevc_mp4toannexb" : "h264_mp4toannexb")
	.addOption("-hls_time", second)
	.addOption("-hls_list_size", "0")
	.addOption("-hls_segment_filename", path.join(streamsDir, "%d.ts"))
	.output(m3u8File)
	.on("end", async () => {
		fs.readFile(m3u8File, "utf8", (err, data) => {
			if (err) {
				console.error("m3u8 文件读取时发生错误:", err);
				return;
			}
			const modifiedData = data.replace(/,\r?\n/g, ",\nstreams/");

			fs.writeFile(m3u8File, modifiedData, "utf8", (err) => {
				if (err) {
					console.error("m3u8 文件写入时发生错误:", err);
					return;
				}
				console.log("切片完成");
			});
		});
	})
	.run();
