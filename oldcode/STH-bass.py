import numpy as np
import pandas as pd
from scipy import optimize
from math import sqrt,log,exp
from datetime import timedelta

#get the time betweet the latest time & the retweet time
def get_delta_df(group):
	return pd.DataFrame({
		'time': (group['time'] - group['time'].min()).apply(lambda dt: dt / timedelta(minutes=1)),
		'original_status_id': group['original_status_id'],
		'original_user_id': group['original_user_id'],
	})

#what time
def create_observation(cascade, time):
	return cascade[cascade['time'] < time.total_seconds() / 60]

#sth_bass estimate
def estimate_y_sth(t,p,q,m,alpha,X,beta,Y):# t is an array
	V = p*m + np.sum(np.multiply(alpha,X)) + np.sum(np.multiply(beta,Y))
	delta = m**2 *(p-q)**2 + 4*m*q*V
	y1= (m*(q-p) + sqrt(delta))/(2*q)
	y2 =(m*(q-p) - sqrt(delta))/(2*q)
	e = np.exp(-sqrt(delta)/(m*q)*t + log(-y1/y2))
	estimate = (y2*e +y1)/(1+e)
	return estimate

#y-estimate_y_sth
def loss_sth(t,p,q,m,alpha,X,beta,Y,y):
	return y- estimate_y_sth(t,p,q,m,alpha,X,beta,Y)

#fit bass_sth
def fit_bass_sth(df,userdata,contentdata):
	posttime = df['time'].values
	count = df.shape[0]
	y = np.arange(count)+1
	alpha = np.random.rand(4)
	beta = np.random.rand(3)
	X = contentdata.loc[df['original_status_id']].values
	Y = userdata.loc[df['original_user_id']].values
	initial = np.concatenate((np.array([0.1,0.1,count]),alpha,beta))
	trained = optimize.least_squares(lambda par:loss_sth(posttime,par[0],par[1],par[2],par[3:7],X,par[7:10],Y,y),initial,bounds=(1e-7,np.inf))
	return pd.Series({
		'p': trained.x[0],
		'q': trained.x[1],
		'm': trained.x[2],
		'alpha':trained.x[3:7],
		'beta':trained.x[7:10],
	})

#compute the y
def estimate_y(t,p,q,m):
	y1 = m
	y2 = -m*p/q
	e = np.exp((-p/q +1)*t+log(q/p))
	return (y2*e+y1)/(1+e)


def loss(t,p,q,m,y):
	return y-estimate_y(t,p,q,m)

#fit_bass model
def fit_bass(df):
	posttime = df['time'].values
	count = df.shape[0]
	y = np.arange(count)+1
	initial = np.array([0.1,0.1,count])
	trained = optimize.least_squares(lambda par:loss(posttime,par[0],par[1],par[2],y),initial,bounds=(1e-7,np.inf))
	return pd.Series({
		'p': trained.x[0],
		'q': trained.x[1],
		'm': trained.x[2]
	})

# for regression
def accuracyreg(prediction, final):
	results = prediction.join(final, how='inner')
	results['se'] = (results['predicted'] - results['size']) ** 2
	results['pe'] = (results['predicted'] - results['size']) / results['size']
	results['ape'] = abs(results['pe'])
	results['var'] = (results['size'] - results['size'].mean()) ** 2
	return results


# for classification tp|fp|tn|fn
def accuracycla(prediction, final, threshold):
	final['popular'] = final['size'].apply(lambda x: x >= threshold)
	prediction['predicted'] = prediction.predicted.apply(lambda x: x >= threshold)
	results = prediction.join(final, how='inner')
	results['tp'] = prediction['predicted'] & final['popular']
	results['fp'] = prediction['predicted'] & ~final['popular']
	results['tn'] = ~prediction['predicted'] & ~final['popular']
	results['fn'] = ~prediction['predicted'] & final['popular']
	return results

#the assess of the predict 
def peek_predict(wcascade, threshold, dataset,timepts=[6, 12, 18, 24],userdata=None,contentdata=None,method='bass'):
	dlist = []

	final = pd.DataFrame(wcascade.groupby('original_status_id').size(), columns={'size', })#original status as index
	resultsall = final.copy()

	for i in timepts:
		print(i)
		pcascade = create_observation(wcascade, timedelta(hours=i))
		if method == 'sth':
			bass_params = pcascade.groupby('original_status_id').apply(lambda df: fit_bass_sth(df,userdata,contentdata))
		else:
			bass_params = pcascade.groupby('original_status_id').apply(fit_bass)
		prediction = bass_params[['m']].rename(columns={'m':'predicted'})
		prediction.to_csv('./data/prediction-{}-{}.csv'.format(dataset,i))
		resultsall[str(i)] = prediction
		resultsreg = accuracyreg(prediction, final)

		resultscla = accuracycla(prediction, final, threshold)
		precision = resultscla.tp.sum() / (resultscla.tp.sum() + resultscla.fp.sum())
		recall = resultscla.tp.sum() / (resultscla.tp.sum() + resultscla.fn.sum())
		# extreme cases
		d = {
			'predicttime': i,
			'mse': resultsreg.se.mean(),
			'medianse': resultsreg.se.median(),
			'mape': resultsreg.ape.mean(),
			'medianape': resultsreg.ape.median(),
			'R2': 1 - resultsreg['se'].sum() / resultsreg['var'].sum(),
			'precision': precision,
			'recall': recall,
			'f1': 2 / (1 / precision + 1 / recall),
		}
		dlist.append(d)
	evaluation = pd.DataFrame(dlist)
	resultsall = resultsall.reset_index()
	return [evaluation, resultsall]

#cascade_file - twitter data
# original_status_id | original_user_id | delta(time between repost and original post| user_id
#user_file - userdata
# user_id | friends_count | followers_count | statuses_count | favourites_count
#content_file contentdata
# original_status_id | length | url | time | hour
#timepts array (1,2,...,24)
#dataset weibo/twitter
#method bass/sth?
def main(cascade_file,user_file,content_file,timepts,dataset='weibo',method='bass'):
	if dataset == 'weibo':# calculate delta
		cascade = pd.read_csv(cascade_file,parse_dates=['time'], infer_datetime_format=True)
		cascade.columns = ['original_status_id', 'original_user_id', 'time', 'user_id']
		cascade_delta = cascade.groupby('original_status_id').apply(get_delta_df)
	else:#twitter has delta
		cascade_delta = pd.read_csv(cascade_file) #delta is float
		cascade_delta.rename(columns={'delta': 'time'}, inplace=True)

	threshold = cascade_delta.groupby('original_status_id').size().quantile(q=0.99, interpolation='nearest')
	# remove initial post times
	wcascade = cascade_delta[cascade_delta['time'] != 0]
	if method =='sth':
		userdata = pd.read_csv(user_file)
		#setting suoyin
		userdata = userdata.set_index('original_user_id')
		#qu chongfu hang
		userdata.drop_duplicates(inplace=True)
		#liyong apply lai diaoyong log 
		#lambda  niming hanshu ;dui suoyou yuansu  qiu log
		userdata = userdata.apply(lambda x: np.log(x+1))
		contentdata = pd.read_csv(content_file,usecols=['original_status_id','length','url','hour'])
		contentdata = contentdata.set_index('original_status_id')
		contentdata.drop_duplicates(inplace=True)
		contentdata = contentdata.apply(lambda x: np.log(x + 1))
		#dui x,y jinxingle quchong  log chuli 
		[evaluation, resultsall] = peek_predict(wcascade, threshold, dataset,timepts,userdata=userdata,contentdata=contentdata,method='sth')
	else:
		[evaluation, resultsall] = peek_predict(wcascade, threshold, dataset,timepts,method='bass')
	evaluation.to_csv('./data/evaluation-twitter-sample.csv',encoding='utf-8',index=False)
	resultsall.to_csv('./data/prediction-twitter-sample.csv',encoding='utf-8',index=False)
	return


main('data/diffusion-delta-twitter-sample.csv','data/twitter-userdata.csv','data/twitter-contentdata.csv',[i + 1 for i in range(24)],dataset='twitter')

# twitter data
# original_status_id | original_user_id | delta(time between repost and original post| user_id

# userdata
# user_id | friends_count | followers_count | statuses_count | favourites_count

# contentdata
# original_status_id | length | url | time | hour
