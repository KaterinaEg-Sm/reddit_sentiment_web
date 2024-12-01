from flask import jsonify
import praw
import pandas as pd
from textblob import TextBlob
import matplotlib.pyplot as plt

import seaborn as sns
from wordcloud import WordCloud, STOPWORDS
import os

# Credentials
client_id = '_Dg7T7G5aQ3WIMFli6d31g'
client_secret = 'gjenP2Q3zzLAI_eukg7v3mbM780kGg'
user_agent = 'my_bot/0.1 by u/No-Cherry-3059'

# Initializing PRAW with the credentials
reddit = praw.Reddit(client_id=client_id,
                     client_secret=client_secret,
                     user_agent=user_agent)

# Set the path where the images will be saved
SAVE_DIR = 'static/images'

# Ensure the directory exists
os.makedirs(SAVE_DIR, exist_ok=True)

# Setting comments and posts limits
post_count_limit = 10
comment_count_limit = 10

# Retrieving posts and associated comments

def api_getdata(SUBREDDIT, WORD):
    print('Funcion - api_getdata')
    subreddit = reddit.subreddit(SUBREDDIT)
    posts = list(subreddit.search(WORD, limit = post_count_limit))
    return posts

def clean_posts(posts):
    print('Funcion - clean_posts')
    PostData_Cleaned = []
    
    for post in posts:
        
        PostData_Cleaned.append({
            'title': post.title,
            'selftext': post.selftext,
            'score': post.score,
            'num_comments': post.num_comments,
            'created': post.created_utc
        }) 
        df_posts =pd.DataFrame(PostData_Cleaned)
    return df_posts


def clean_comments(posts):
    print('Funcion - clean_comments')

    PostComments_Cleaned = []

    for post in posts:
            
        comment_count = 0 
        for comment in post.comments:  
            if isinstance(comment, praw.models.MoreComments):
                continue 
            if comment_count<comment_count_limit:
                    PostComments_Cleaned.append({
                        'title': post.title, 
                        'selftext': post.selftext,
                        'num_comments': post.num_comments,
                        'comment': comment.body,
                        'created': post.created_utc 
                    })
            comment_count += 1

    df_comments =pd.DataFrame(PostComments_Cleaned) 
    print('Funcion - clean_comments - END')
    return df_comments
   




# Data cleaning 
def clean_df(df, WORD):
    print('Funcion - clean_df')
    df['date'] = pd.to_datetime(df['created'], unit='s').dt.date
    df = df.drop('created', axis=1)
    df['selftext'] = df['selftext'].fillna(' ')
    df = df[df['title'].str.contains(WORD, case=False)].copy()
    return df

# Textblob sentiment analysis function
def analyze_sentiment(text):
    print('Funcion - analyze_sentiment')
    blob = TextBlob(text)
    return blob.sentiment.polarity, blob.sentiment.subjectivity

# Add columns to df after textblob analysis
def add_sentiment_columns(df, column_to_analyse, polarity_column_name='polarity', subjectivity_column_name='subjectivity'):
    print('Funcion - add_sentiment_columns')
    df[[polarity_column_name, subjectivity_column_name]] = df[column_to_analyse].apply(lambda x: pd.Series(analyze_sentiment(x)))
    return df

#Plotting textblob viz
def get_chart(df, column_name, chart_name, save_name):    
    print('Funcion - get_chart')
    plt.figure(figsize=(10, 6))
    sns.histplot(df[column_name], bins=20, kde=True)
    plt.title(chart_name)
    plt.xlabel('Polarity')
    plt.ylabel('Frequency')
    #plt.show()
        # Define the path where the image will be saved
    filename = save_name + '.png'
    filepath = os.path.join(SAVE_DIR, filename)

    # Save the plot to the specified file path
    plt.savefig(filepath)
    plt.close() 


# Defining a function to apply Word Cloud analysis

def cloud_analysis(column_to_analyse, save_name):
    print('Funcion - cloud_analysis')
    extra_stop = {'n', 'nk', 's' , 'yes', 'welcome', 'm', 'deleted' , 'thank'}
    stopwords = STOPWORDS.union(extra_stop)
    title_cloud = WordCloud(stopwords = stopwords).generate(column_to_analyse.to_string())
    plt.imshow(title_cloud, interpolation = 'bilinear')
    plt.axis('off')
    #plt.show()
        # Define the path where the image will be saved
    filename = save_name + '.png'
    filepath = os.path.join(SAVE_DIR, filename)
    #plt.imsave(filepath, title_cloud.to_array())
    # Save the plot to the specified file path
    plt.savefig(filepath)
    plt.close() 

#Most common sentiment
def sentiment_type(x):
    print('Funcion - sentiment_type')
    if x == 0:
        return ('Neutral')
    elif x > 0:
        return ('Positive')
    else:
        return ('Negative')
    
def get_description_sentiment(df, column):
    print('Funcion - get_description_sentiment')
    df['sentiment'] = df[column].apply(lambda x: pd.Series(sentiment_type(x)))
    sentiment_counts = df['sentiment'].value_counts()
    most_freq_sentiment = sentiment_counts.idxmax() 
    print ('Most frequent ',column,' sentiment:')
    print (most_freq_sentiment)
    return most_freq_sentiment

def get_mostusedwords(df_comments):
    extra_stop = {'n', 'nk', 's' , 'yes', 'welcome', 'm', 'deleted' , 'thank', 'hi', 'everyone', 've', 't', '/t'}
    stopwords = STOPWORDS.union(extra_stop)
    comments_series = df_comments['comment']
    comments_cloud = WordCloud(stopwords=stopwords).generate(comments_series.to_string())
    freq_word_comment = comments_cloud.words_
    top_5_words = sorted(freq_word_comment.items(), key=lambda x: x[1], reverse=True)[:5]
    print ('Top 5 most frequent words in the comment section:')
    for word,_ in top_5_words:
        print (word)
    return top_5_words

def datacheck(SUBREDDIT, WORD):
    print('Funcion - datacheck')
    redditapi_posts = api_getdata(SUBREDDIT, WORD)

    post_dataframe = clean_posts(redditapi_posts)
    comment_dataframe = clean_comments(redditapi_posts)

    post_clean=clean_df(post_dataframe, WORD)
    comment_clean=clean_df(comment_dataframe, WORD)

    update_post_df = add_sentiment_columns(post_clean, 'selftext', 'selftext polarity', 'selftext subjectivity')
    update_comment_df =add_sentiment_columns(comment_clean, 'comment', 'comment polarity', 'comment subjectivity')

    attitude_result = get_description_sentiment(update_comment_df, 'comment polarity')
    attitude_result_post = get_description_sentiment(update_post_df, 'selftext polarity')


    #get_chart(update_post_df, 'selftext polarity', 'Distribution of Post Selftext Polarity', 'chart_2')
    #get_chart(update_comment_df, 'comment polarity', 'Distribution of Post Comments Polarity', 'chart_1')

    cloud_analysis(update_comment_df['comment'], 'wordcloud_1')

    Top5Words = get_mostusedwords(update_comment_df)

    return jsonify({
        'attitude_result': attitude_result,
        'attitude_result_post': attitude_result_post,
        'top_words' : Top5Words,
        'topwords_1': Top5Words[0][0],
        'topwords_2': Top5Words[1][0],
        'topwords_3': Top5Words[2][0],
        'topwords_4': Top5Words[3][0],
        'topwords_5': Top5Words[4][0]
    })