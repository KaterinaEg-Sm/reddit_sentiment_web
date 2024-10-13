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


post_count_limit = 10
comment_count_limit = 100


def datacheck(SUBREDDIT, WORD):
    # Retrieving posts 
    print("API - Request Data")
    subreddit = reddit.subreddit(SUBREDDIT)
    print("API - Response")
    posts = list(subreddit.search(WORD, limit = post_count_limit))

    Post_Cleaned = clean_Posts(posts)
    Comments_Cleaned = clean_Comments(posts)
   
   
    print("API - Loading Dataframes")         
    df_comments =pd.DataFrame(Comments_Cleaned) 
    df_posts =pd.DataFrame(Post_Cleaned) 
    print("API - End")      

    df_comments['date'] = pd.to_datetime(df_comments['created'], unit='s').dt.date
    df_posts['date'] = pd.to_datetime(df_posts['created'], unit='s').dt.date
    df_comments = df_comments.drop('created', axis=1)
    df_posts = df_posts.drop('created', axis=1)
    

    ordinary_posts = df_posts[df_posts['title'].str.contains(WORD, case=False)].copy()

    ordinary_posts['selftext'] = ordinary_posts['selftext'].fillna(' ')
    ordinary_posts[['polarity post', 'subjectivity post']] = ordinary_posts['title'].apply(lambda x: pd.Series(analyze_sentiment(x)))
    ordinary_posts[['polarity selftext', 'subjectivity selftext']] = ordinary_posts['selftext'].apply(lambda x: pd.Series(analyze_sentiment(x)))
    ordinary_posts['selftext sentiment'] = ordinary_posts ['polarity selftext'].apply(lambda x: pd.Series(sentiment_type(x)))
    
    get_chart(ordinary_posts, 'polarity selftext', 'Distribution of Post Selftext Polarity', 'chart_1')  
    # get_chart(comments, 'polarity comment', 'Distribution of Post Comments Polarity', 'chart_2')  
    attitude_result = get_comment_sentiment(df_comments, WORD) 
    top_5 = get_mostusedwords(df_comments)
 
    return jsonify({
        'post_count': len(Post_Cleaned),
        'comment_count': len(Comments_Cleaned),        
        'attitude_result': attitude_result,
        'topwords_1': top_5[0][0],
        'topwords_2': top_5[1][0],
        'topwords_3': top_5[2][0],
        'topwords_4': top_5[3][0],
        'topwords_5': top_5[4][0],
    })


def clean_Posts(posts):
    print("API - Clean Post Data")
    Post_Cleaned = [] 
    for post in posts:    
        Post_Cleaned.append({
            'title': post.title,
            'selftext': post.selftext,
            'score': post.score,
            'num_comments': post.num_comments,
            'created': post.created_utc
        }) 
    return Post_Cleaned


def clean_Comments(posts):
    print("API - Clean Comment Data")
    Comments_Cleaned = []

    for post in posts:        
        comment_count = 0 
        post.comments.replace_more(limit=1) 
        for comment in post.comments.list():  
            print(post.title)                
            if isinstance(comment, praw.models.MoreComments):
                    continue 
            if comment_count<comment_count_limit:
                Comments_Cleaned.append({
                    'title': post.title, 
                    'selftext': post.selftext,
                    'num_comments': post.num_comments,
                    'comment': comment.body,
                    'created': post.created_utc 
                })  
                comment_count += 1
            else:
                break  # Stop the loop after comment count limit
            # try:

            # except:
            #     print("An exception occurred")
               
            
       
    print("API - Comment Data Cleaned")
    return Comments_Cleaned

    
    

def analyze_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.polarity, blob.sentiment.subjectivity   

def get_post_description_sentiment(posts):       
    sentiment_selftext_counts = posts['selftext sentiment'].value_counts()
    most_freq_selftext_sentiment = sentiment_selftext_counts.idxmax()
    print ('Most frequent selftext sentiment:')
    print (most_freq_selftext_sentiment)
    return most_freq_selftext_sentiment


def get_comment_sentiment(df_comments, GET_WORD):       
    comments = df_comments[df_comments['title'].str.contains(GET_WORD, case=False)].copy()
    comments[['polarity comment', 'subjectivity comment']] = comments['comment'].apply(lambda x: pd.Series(analyze_sentiment(x)))
    comments['comment sentiment'] = comments ['polarity comment'].apply(lambda x: pd.Series(sentiment_type(x)))
    sentiment_comment_counts = comments['comment sentiment'].value_counts()
    most_freq_comment_sentiment = sentiment_comment_counts.idxmax()
    print (most_freq_comment_sentiment)
    return most_freq_comment_sentiment

    
def sentiment_type(x):
    if x == 0:
        return ('Neutral')
    elif x > 0:
        return ('Positive')
    else:
        return ('Negative')


def get_mostusedwords(df_comments):
    extra_stop = {'n', 'nk', 's' , 'yes', 'welcome', 'm', 'deleted' , 'thank', 'hi', 'everyone', 've'}
    stopwords = STOPWORDS.union(extra_stop)
    comments_series = df_comments['comment']
    comments_cloud = WordCloud(stopwords=stopwords).generate(comments_series.to_string())
    freq_word_comment = comments_cloud.words_
    top_5_words = sorted(freq_word_comment.items(), key=lambda x: x[1], reverse=True)[:5]
    print ('Top 5 most frequent words in the comment section:')
    for word,_ in top_5_words:
        print (word)
    return top_5_words




def get_chart(df_posts, column_name, chart_name, save_name):    
    plt.figure(figsize=(10, 6))
    sns.histplot(df_posts[column_name], bins=20, kde=True)
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