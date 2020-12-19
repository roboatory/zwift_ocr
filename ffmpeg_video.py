import os
import subprocess
import shutil

# note: need to have ffmpeg installed!
class Video_Editing:
	def __init__(self, video_name, path):
		self.video_name = video_name
		self.path = path
		os.chdir(self.path)
	
	def slice_video(self, start_time, duration):
		new_video_name = "sliced " + self.video_name

		# see "https://trac.ffmpeg.org/wiki/Seeking" for more information
		ffmpeg_slice = ["ffmpeg", "-ss", start_time, "-i", self.video_name, 
			"-to", duration, "-c", "copy", new_video_name]
		subprocess.call(ffmpeg_slice)

	def change_frame_rate(self, fps):
		new_video_name = str(fps) + " fps " + self.video_name

		# see "https://trac.ffmpeg.org/wiki/ChangingFrameRate" for more information
		ffmpeg_change_frame_rate = ["ffmpeg", "-i", self.video_name, "-filter:v", 
			"fps=fps=" + str(fps), new_video_name]
		subprocess.call(ffmpeg_change_frame_rate)

	def concat_video(self, video2_name):
		with open("mylist.txt", "w") as f: 
			f.write("file " + "'" + self.video_name + "'" + "\n")
			f.write("file " + "'" + video2_name + "'")

		# see "https://trac.ffmpeg.org/wiki/Concatenate" for more information
		ffmpeg_combine_videos = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", 
			"mylist.txt", "-c", "copy", "final_video.mp4"]
		subprocess.call(ffmpeg_combine_videos)

	def crop_video_size(self, width, height, x, y):
		crop_dimensions = (str(width) + ":" + str(height) + ":" + str(x) + ":" + str(y))

		# see "https://ffmpeg.org/ffmpeg-filters.html#crop" for more information
		ffmpeg_crop_video = ["ffmpeg", "-i", self.video_name, "-vf", 
			"crop=" + crop_dimensions, "-c:a", "copy", "cropped.mp4"]
		subprocess.call(ffmpeg_crop_video)

	def split_into_frames(self, output_path, fps):
		# see ffmpeg's documentation on the fps video filter for more information
		ffmpeg_split_video = ["ffmpeg", "-i", self.video_name, "-vf", "fps=" + 
			str(fps), "capture%d.jpg"]
		subprocess.call(ffmpeg_split_video)

		for file in os.listdir(self.path):
			if file.endswith(".jpg"):
				shutil.move(self.path + "/" + file, output_path)

