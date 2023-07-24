const ffmpeg = require("fluent-ffmpeg");
const sharp = require("sharp");
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
		description: "间隔描述",
		type: "number",
		default: 1,
	})
	.option("width", {
		alias: "w",
		description: "每张图宽度",
		type: "number",
		default: 300,
	})
	.option("columns", {
		alias: "c",
		description: "每页行数",
		type: "number",
		default: 6,
	})
	.option("rows", {
		alias: "r",
		description: "每页列数",
		type: "number",
		default: 6,
	})
	.help().argv;

const inputVideo = argv.input;
const second = argv.second;
const width = argv.width;

const columns = argv.columns;
const rows = argv.rows;
const count = columns * rows;

const videoName = path.basename(inputVideo, path.extname(inputVideo));
const outputFolder = path.join(path.dirname(inputVideo), videoName);

const framesDir = path.join(outputFolder, "frames");
if (!fs.existsSync(framesDir)) {
	fs.mkdirSync(framesDir, { recursive: true });
}

const thumbsDir = path.join(outputFolder, "thumbs");
if (!fs.existsSync(thumbsDir)) {
	fs.mkdirSync(thumbsDir, { recursive: true });
}

ffmpeg(inputVideo)
	.outputOptions(`-vf fps=1/${second},scale=${width}:-1`)
	.output(path.join(framesDir, "%8d.png"))
	.on("end", async () => {
		console.log("Frames extracted");

		fs.readdir(framesDir, async (err, files) => {
			if (err) throw err;

			if (files.length === 0) {
				console.log("No frames were extracted");
				return;
			}

			const imagePromises = files.map((file) => sharp(path.join(framesDir, file)).resize(width).toBuffer());

			try {
				// probably don't have to do this...
				const images = await Promise.all(imagePromises);
				const imageHeights = images.map((image) =>
					sharp(image)
						.metadata()
						.then((metadata) => metadata.height)
				);
				const imageHeightsResolved = await Promise.all(imageHeights);
				const height = Math.max(...imageHeightsResolved);

				const imageSheets = Array.from({ length: Math.ceil(images.length / count) }, (_, index) => images.slice(index * count, (index + 1) * count));

				for (let i = 0; i < imageSheets.length; i++) {
					await sharp({
						create: {
							width: width * columns,
							height: height * rows,
							channels: 3,
							background: { r: 0, g: 0, b: 0 },
						},
					})
						.composite(
							imageSheets[i].map((image, i) => ({
								input: image,
								left: (i % columns) * width,
								top: Math.floor(i / rows) * height,
							}))
						)
						.toFile(path.join(thumbsDir, i + ".jpg"));
				}
				console.log("Tile image created successfully");

				const vttFile = fs.createWriteStream(path.join(outputFolder, "thumbs.vtt"));
				vttFile.write("WEBVTT\n\n");

				var frames = 0;
				imageSheets.map((sheets, i) => {
					sheets.map((image, j) => {
						const startTime = new Date(second * frames * 1000).toISOString().substr(11, 12);
						const endTime = new Date(second * (frames++ + 1) * 1000).toISOString().substr(11, 12);
						const position = {
							x: (j % columns) * width,
							y: Math.floor(j / rows) * height,
						};

						vttFile.write(`${startTime} --> ${endTime}\n`);
						vttFile.write(`thumbs/${i}.jpg#xywh=${position.x},${position.y},${width},${height}\n\n`);
					});
				});

				vttFile.end();
				console.log("VTT file created successfully");
			} catch (err) {
				console.log(`Error creating tile image: ${err.message}`);
			} finally {
				fs.rmSync(framesDir, { recursive: true });
			}
		});
	})
	.run();
