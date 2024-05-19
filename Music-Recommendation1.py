import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st

music_df = pd.read_csv("musicdata.csv")


# Function to calculate weighted popularity scores based on release date
def calculate_weighted_popularity(release_date):
    # Convert the release date to datetime object
    release_date = datetime.strptime(release_date, '%Y-%m-%d')

    # Calculate the time span between release date and today's date
    time_span = datetime.now() - release_date

    # Calculate the weighted popularity score based on time span (e.g., more recent releases have higher weight)
    weight = 1 / (time_span.days + 1)

    return weight


scaler = MinMaxScaler()

music_features = music_df[['Danceability', 'Energy', 'Key', 'Loudness', 'Mode',
       'Speechiness', 'Acousticness', 'Instrumentalness', 'Liveness',
       'Valence', 'Tempo']].values

music_features_scaled = scaler.fit_transform(music_features)


# Function to get content-based recommendations based on music features
def content_based(input_song_name, num_recom = 5):
  if input_song_name not in music_df['Track Name'].values:
    print("The song '{input_song_name}' is not found in the dataset. Please provide a valid song name.")
    return

  # Get the index of the input song in the music DataFrame
  input_song_index = music_df[music_df['Track Name'] == input_song_name].index[0]

  # Calculate the similarity scores based on music features (cosine similarity)
  similarity_scores = cosine_similarity([music_features_scaled[input_song_index]], music_features_scaled)

  # Get the indices of the most similar songs
  similar_song_indices = similarity_scores.argsort()[0][::-1][1 : num_recom + 1]

  # Get the names of the most similar songs based on content-based filtering
  content_based_recommendations = music_df.iloc[similar_song_indices][['Track Name', 'Artists', 'Album Name', 'Release Date', 'Popularity']]

  return content_based_recommendations
    
  

# Function to get hybrid recommendations
def hybrid_recommendations(input_song_name, num_recom=5, alpha=0.5):
    if input_song_name not in music_df['Track Name'].values:
        print(f"'{input_song_name}' not found in the dataset. Please enter a valid song name.")
        return

    # Get content-based recommendations
    content_based_rec = content_based(input_song_name, num_recom)

    # Check if content_based_rec is a DataFrame
    if not isinstance(content_based_rec, pd.DataFrame):
        print("Content-based recommendations are not available.")
        return

    # Get the popularity score of the input song
    popularity_score = music_df.loc[music_df['Track Name'] == input_song_name, 'Popularity'].values[0]

    # Calculate the weighted popularity score
    weighted_popularity_score = popularity_score * calculate_weighted_popularity(music_df.loc[music_df['Track Name'] == input_song_name, 'Release Date'].values[0])

    # Combine content-based and popularity-based recommendations based on weighted popularity
    hybrid_recommendations = content_based_rec.copy()  
    hybrid_recommendations = pd.concat([hybrid_recommendations, pd.DataFrame({
        'Track Name': [input_song_name],
        'Artists': [music_df.loc[music_df['Track Name'] == input_song_name, 'Artists'].values[0]],
        'Album Name': [music_df.loc[music_df['Track Name'] == input_song_name, 'Album Name'].values[0]],
        'Release Date': [music_df.loc[music_df['Track Name'] == input_song_name, 'Release Date'].values[0]],
        'Popularity': [weighted_popularity_score]
    })], ignore_index=True)

    # Sort the hybrid recommendations based on weighted popularity score
    hybrid_recommendations = hybrid_recommendations.sort_values(by='Popularity', ascending=False)

    # Remove the input song from the recommendations
    hybrid_recommendations = hybrid_recommendations[hybrid_recommendations['Track Name'] != input_song_name]

    return hybrid_recommendations
    





# Set page title and favicon
st.set_page_config(page_title="Music Recommendation App", page_icon="🎵")

# Define app layout
st.title("🎶 Music Recommendation Dashboard")
st.markdown("---")

# Input section
st.sidebar.header("Select Song")
input_option = st.sidebar.radio("Choose Input Method:", ["Enter Song Name", "Select from List"])

if input_option == "Enter Song Name":
    input_song_name = st.sidebar.text_input("Enter Song Name:")
else:
    input_song_name = st.sidebar.selectbox("Select Song:", music_df['Track Name'].unique())

# Recommendation type selection
st.sidebar.header("Select Recommendation Type")
recommendation_type = st.sidebar.radio("", ["Content-based", "Hybrid"])

# Submit button
if st.sidebar.button("Get Recommendations"):
    with st.spinner("Loading Recommendations..."):
        if recommendation_type == "Content-based":
            recommendations = content_based(input_song_name)
        elif recommendation_type == "Hybrid":
            recommendations = hybrid_recommendations(input_song_name)
    
    # Display recommendations
    st.header("🎵 Recommendations")
    if recommendations is not None and not recommendations.empty:
        st.dataframe(recommendations.style.set_properties(**{'text-align': 'center'}))
    else:
        st.error("No recommendations available.")

# Footer
st.markdown("---")
st.sidebar.markdown("Made with ❤️ by Ankit")
