import pandas as pd 
import matplotlib.pyplot as plt 
import numpy as np
from scipy import signal, stats
import seaborn as sns
import matplotlib

# FEA features for emotional analysis 
# (note: Anger through Attention are the emotions of interest)
features = ["Anger", "Contempt", "Disgust", "Fear", "Joy", "Sadness", 
	"Surprise", "Engagement", "Valence", "Attention", "Brow Furrow", 
	"Brow Raise", "Cheek Raise", "Chin Raise", "Dimpler", "Eye Closure", 
	"Eye Widen", "Inner Brow Raise", "Jaw Drop", "Lip Corner Depressor", 
	"Lip Press", "Lip Pucker", "Lip Stretch", "Lip Suck", "Lid Tighten", 
	"Mouth Open", "Nose Wrinkle", "Smile", "Smirk", "Upper Lip Raise", "Pitch", 
	"Yaw", "Roll", "Interocular Distance"]

def create_emotions_df(input_path):
	# read in and clean emotions dataset
	emotions_df = pd.read_csv(input_path, skiprows = 27, names = features, 
		skipfooter = 2, engine = "python")
	emotions_df = emotions_df.reset_index().set_index("level_1").rename_axis("Milliseconds")
	emotions_df.drop(columns = emotions_df.columns[0:9], inplace = True)

	return emotions_df

def plot_emotions(emotions_df, output_path = None):
	prev_feature = 0

	# slice the dataframe every two columns and plot on a new figure 
	# until all columns are utilized
	for curr_feature in range(2, len(features) + 1, 2):
		fig, ((ax1), (ax2)) = plt.subplots(nrows = 2, ncols = 1, figsize = (18, 8))

		sliced_df = emotions_df.iloc[:, prev_feature:curr_feature]
		prev_feature = curr_feature

		sliced_df.plot(subplots = True, color = {"green", "orange"}, 
			title = list(sliced_df.columns), legend = False, sharex = False, 
			ax = (ax1, ax2))

		ax1.set_xlabel("Milliseconds", labelpad = 3)
		ax2.set_xlabel("Milliseconds", labelpad = 3)

		ax1.set_ylabel("FEA Metric", labelpad = 3)
		ax2.set_ylabel("FEA Metric", labelpad = 3)
		
		plt.tight_layout(pad = 3)

		#fig.savefig(output_path + "/" + str(sliced_df.columns) + ".pdf")
		plt.show()

def create_power_hr_df(hr_input_path, pwr_input_path):
	heart_rate_df = pd.read_csv(hr_input_path, sep = "-", 
		header = None, names = ["File", "HR"]).rename_axis("seconds")
	heart_rate_df.drop(columns = ["File"], inplace = True)

	power_df = pd.read_csv(pwr_input_path, sep = "-", 
		header = None, names = ["File", "Power"]).rename_axis("seconds")
	power_df.drop(columns = ["File"], inplace = True)

	merged_df = (heart_rate_df.merge(power_df, on = "seconds"))
	return merged_df

def clean_power_hr_df(hr_input_path, pwr_input_path):
	merged_df = create_power_hr_df(hr_input_path, pwr_input_path)

	# regex expression adopted from this post
	# https://www.journaldev.com/23763/python-remove-spaces-from-string
	merged_df.replace(r'^\s*$', np.nan, inplace = True, regex = True)

	# regex expression adopted from this forum
	# https://stackoverflow.com/questions/38640791/remove-spaces-between-numbers-in-a-string-in-python
	merged_df.replace(r'\s*(\d)\s+(\d)', r'\1\2', inplace = True, regex = True)

	merged_df = merged_df.apply(pd.to_numeric).dropna(axis = 0)

	# implement z score to detect outliers in the tesseract dataset 
	# (code derived from TDS online Medium publication, author: Natasha Sharma)
	# https://towardsdatascience.com/ways-to-detect-and-remove-the-outliers-404d16608dba 
	z = np.abs(stats.zscore(merged_df))
	cleaned_df = merged_df[(z < 3).all(axis = 1)]

	# smooth data to counteract influence of incorrect data samples
	pd.options.mode.chained_assignment = None
	cleaned_df["ewm_HR"] = cleaned_df["HR"].ewm(alpha = 0.1).mean()
	cleaned_df["ewm_Power"] = cleaned_df["Power"].ewm(alpha = 0.1).mean()
	
	return cleaned_df

def plot_tesseract_results(cleaned_df, output_path = None):
	'''plots data from the tesseract dataframe'''
	fig, [ax1, ax2] = plt.subplots(nrows = 2, ncols = 1, figsize = (18, 8))

	cleaned_df["HR"].plot(ax = ax1, title = "Heart Rate (BPM)", legend = False, 
		color = "red")
	cleaned_df["ewm_HR"].plot(ax = ax1, color = "black")

	cleaned_df["Power"].plot(ax = ax2, title = "Power (W)", legend = False, 
		color = "blue")
	cleaned_df["ewm_Power"].plot(ax = ax2, color = "black")
	
	ax1.set_ylabel("BPM", labelpad = 10)
	ax2.set_ylabel("W", labelpad = 10)

	plt.tight_layout(pad = 3) # increase spacing between subplots
	plt.tick_params(axis = "x", rotation = 0)

	fig.suptitle("Title", x = 0.5155, y = 0.99)
	#fig.savefig(output_path + "/tesseract_plot.pdf")
	plt.show()

def generate_subject(emotions_df, power_hr_df):
	# group data every minute and merge emotions, power 
	# for correlation analysis
	emotions = emotions_df.iloc[:, :10]
	emotions.index = (np.array(emotions.index) / 60000).astype(int)
	new_emotions_df = (emotions.groupby(emotions.index).mean().
		rename_axis("minutes"))

	power_hr_df.index = power_hr_df.index.astype(int)
	power_hr_df.index = (np.array(power_hr_df.index) / 60).astype(int)
	new_pwr_df = (power_hr_df.groupby(power_hr_df.index).mean().
		drop(["ewm_HR", "ewm_Power"], axis = 1).rename_axis("minutes"))

	subject = new_pwr_df.merge(new_emotions_df, on = "minutes")
	return subject

def generate_scatter_plots(subject):
	# plot scatter plot of each emotion compared to power/hr
	fig, axes = plt.subplots(5, 2, figsize = (8, 8), sharex = True)
	plt.subplots_adjust(left = 0.125, right = 0.9, bottom = 0.1, top = 0.9, 
		wspace = 0.2, hspace = 0.4)
	plt.suptitle("Enter Title Here", y = 0.99)
	plt.tight_layout(pad = 2)
	
	emotional_feature = 2
	for ax in axes:
		ax[0].scatter(subject["HR"], 
			subject.iloc[:, emotional_feature], color = "black")
		ax[0].set_title(subject.columns[emotional_feature])
		ax[0].tick_params(length = 0, axis = "x")
		emotional_feature += 1

		ax[1].scatter(subject["HR"], 
			subject.iloc[:, emotional_feature], color = "black")
		ax[1].set_title(subject.columns[emotional_feature])
		ax[1].tick_params(length = 0, axis = "x")
		emotional_feature += 1

	axes[4][0].set_xlabel("HR")
	axes[4][1].set_xlabel("HR")
	
	plt.show()

def even_more_plots(subject):
	pearson_correlations = subject.corr(method = "pearson")
	correlation = pearson_correlations.loc["Valence", "Power"]

	# generate scatter plot and fitted linear regression between two features
	plt.figure(1)
	sns.regplot(subject["Valence"], subject["Power"], color = "black")
	plt.xlabel("Valence", labelpad = 7)
	plt.ylabel("Power (W)", labelpad = 7)
	plt.suptitle("Title", x = 0.5155, y = 0.95)

	# generate heat map of the pearson correlations
	plt.figure(2, figsize = (8, 7))
	plt.subplots_adjust(left = 0.125, right = 0.9, bottom = 0.16, top = 0.9, 
		wspace = 0.2, hspace = 0.4)
	sns.heatmap(pearson_correlations)
	plt.suptitle("Title", x = 0.5155, y = 0.95)

	# generate plot of engagement and attention over time
	plt.figure(3)
	subject["Engagement"].plot(color = "green")
	subject["Attention"].plot(color = "black")
	plt.legend()
	plt.xlabel("Minutes", labelpad = 7)
	plt.ylabel("FEA Metric", labelpad = 7)
	plt.suptitle("Title", x = 0.5155, y = 0.95)

	plt.show()

def percentage_video_captured(orig_df, mod_df):
	return len(mod_df) / len(orig_df)

def main():
	em_input_path = None
	hr_input_path = None
	pwr_input_path = None
