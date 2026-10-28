
# ============================================================
# BOOKVERSERA - AI BOOK DISCOVERY SYSTEM
# Class 12 Artificial Intelligence / Machine Learning Project
# ============================================================

# SECTION 1: IMPORT LIBRARIES
# Pandas handles data, NumPy handles numerical operations,
# Matplotlib creates graphs, and Scikit-learn provides ML tools.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, confusion_matrix


# ============================================================
# SECTION 2: LOAD AND PREPROCESS DATA
# Read books.csv, clean essential fields and remove duplicates.
# ============================================================

try:
    df = pd.read_csv("books.csv")
except FileNotFoundError:
    print("books.csv not found. Run make_dataset.py first.")
    raise SystemExit

required_columns = [
    "Title", "Author", "Genre", "Year", "Rating", "Description"
]

missing = [col for col in required_columns if col not in df.columns]

if missing:
    print("Missing required columns:", missing)
    raise SystemExit

# Remember the original missing-value counts for dataset exploration.
original_missing = df.isnull().sum()

# Clean text columns and handle missing values.
for col in ["Title", "Author", "Genre", "Description"]:
    df[col] = df[col].fillna("").astype(str).str.strip()

df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")

# Remove rows that lack a title, author or genre.
df = df[
    (df["Title"] != "") &
    (df["Author"] != "") &
    (df["Genre"] != "")
].copy()

# Keep one record per title.
df = df.drop_duplicates(subset="Title", keep="first")

# Normalise genre names and replace missing ratings with the mean.
df["Genre"] = df["Genre"].str.title()

if df["Rating"].notna().any():
    df["Rating"] = df["Rating"].fillna(df["Rating"].mean())

df = df.reset_index(drop=True)

if df.empty:
    print("The dataset contains no usable book records.")
    raise SystemExit


# ============================================================
# SECTION 3: BUILD THE RECOMMENDATION SYSTEM
# TF-IDF converts book text into numerical vectors.
# Cosine similarity measures similarity between those vectors.
# ============================================================

# Combine titles, authors, genres and subjects/descriptions.
df["Tags"] = (
    df["Title"] + " " +
    df["Author"] + " " +
    df["Genre"] + " " +
    df["Description"]
)

recommendation_vectorizer = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1, 2)
)

book_vectors = recommendation_vectorizer.fit_transform(df["Tags"])

# Calculate the similarity between every pair of books.
similarity_matrix = cosine_similarity(book_vectors)

# Save the latest recommendations for a graph.
last_recommendations = pd.DataFrame(
    columns=["Title", "Author", "Similarity"]
)


# ============================================================
# SECTION 4: TRAIN THE GENRE PREDICTION MODEL
# Use a genuine train-test split and Multinomial Naive Bayes.
# Evaluation is performed on data excluded from training.
# ============================================================

genre_model_ready = False
genre_accuracy = 0.0
confusion = None
y_test = None
y_pred = None
X_train = None
X_test = None
genre_vectorizer = None
genre_model = None

# Use book titles and available subject text as input features.
genre_text = df["Title"] + " " + df["Description"]
genre_labels = df["Genre"]

# A class needs enough records to appear in both data splits.
genre_counts = genre_labels.value_counts()

if len(df) >= 16 and genre_counts.min() >= 4:

    # Reserve 25% of records for testing.
    X_train_text, X_test_text, y_train, y_test = train_test_split(
        genre_text,
        genre_labels,
        test_size=0.25,
        random_state=42,
        stratify=genre_labels
    )

    # Learn vocabulary from training data only.
    genre_vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2)
    )

    X_train = genre_vectorizer.fit_transform(X_train_text)
    X_test = genre_vectorizer.transform(X_test_text)

    # Train the classifier.
    genre_model = MultinomialNB()
    genre_model.fit(X_train, y_train)

    # Predict genres for unseen test records.
    y_pred = genre_model.predict(X_test)

    # Calculate actual evaluation results.
    genre_accuracy = accuracy_score(y_test, y_pred)

    confusion = confusion_matrix(
        y_test,
        y_pred,
        labels=genre_model.classes_
    )

    genre_model_ready = True

print("\nBookVersera is ready!")
print("Books loaded:", len(df))
print("Recommendation model: READY")
print(
    "Genre prediction model:",
    "READY" if genre_model_ready else
    "NOT READY - collect more books per genre"
)


# ============================================================
# SECTION 5: DISPLAY BOOKS
# Show all available books and their basic details.
# ============================================================

def display_books():
    print("\n========== BOOK COLLECTION ==========")

    columns = ["Title", "Author", "Genre", "Year", "Rating"]
    print(df[columns].to_string(index=False))
    print("\nTotal books:", len(df))


# ============================================================
# SECTION 6: SEARCH BOOKS
# Find books using a title or part of a title.
# ============================================================

def search_books():
    query = input("\nEnter a title or keyword: ").strip()

    if not query:
        print("Enter a search term.")
        return

    # Search without case sensitivity or regular-expression matching.
    results = df[
        df["Title"].str.contains(
            query, case=False, regex=False, na=False
        )
    ]

    if results.empty:
        print("No matching books found.")
    else:
        print("\n========== SEARCH RESULTS ==========")
        print(
            results[
                ["Title", "Author", "Genre", "Year", "Rating"]
            ].to_string(index=False)
        )


# ============================================================
# SECTION 7: RECOMMEND SIMILAR BOOKS
# Rank books using their cosine similarity scores.
# ============================================================

def recommend_books():
    global last_recommendations

    query = input("\nEnter a book title: ").strip()

    if not query:
        print("Enter a book title.")
        return

    matches = df[
        df["Title"].str.contains(
            query, case=False, regex=False, na=False
        )
    ]

    if matches.empty:
        print("Book not found. Try another title.")
        return

    # Ask the user to select a book if several titles match.
    if len(matches) > 1:
        print("\nMatching books:")
        for index, book in matches.iterrows():
            print(f"{index}. {book['Title']} - {book['Author']}")

        try:
            book_index = int(input("Enter the index of your book: "))
        except ValueError:
            print("Please enter a valid index.")
            return

        if book_index not in matches.index:
            print("Invalid selection.")
            return
    else:
        book_index = matches.index[0]

    # Obtain the selected book's similarity scores.
    scores = similarity_matrix[book_index]

    # Rank from highest to lowest and exclude the selected book.
    ranked_indices = np.argsort(scores)[::-1]
    ranked_indices = [
        i for i in ranked_indices if i != book_index
    ][:5]

    last_recommendations = pd.DataFrame({
        "Title": df.loc[ranked_indices, "Title"].values,
        "Author": df.loc[ranked_indices, "Author"].values,
        "Similarity": scores[ranked_indices]
    })

    print("\n========== BOOKVERSERA RECOMMENDS ==========")
    print("Selected:", df.loc[book_index, "Title"])

    for number, (_, book) in enumerate(
        last_recommendations.iterrows(), start=1
    ):
        print(f"\n{number}. {book['Title']}")
        print(f"   Author: {book['Author']}")
        print(f"   Similarity score: {book['Similarity']:.3f}")

    # Plot the scores of the recommended books.
    plot_recommendation_scores()


# ============================================================
# SECTION 8: PREDICT BOOK GENRE
# Predict a likely genre from a title and a short description.
# ============================================================

def predict_genre():
    if not genre_model_ready:
        print("\nGenre model is not ready.")
        print("Run make_dataset.py and collect more examples per genre.")
        return

    print("\n========== GENRE PREDICTION ==========")

    title = input("Enter book title: ").strip()
    description = input("Enter book description: ").strip()

    text = (title + " " + description).strip()

    if not text:
        print("Enter a title or description.")
        return

    # Apply the same text transformation used during training.
    input_vector = genre_vectorizer.transform([text])

    # Predict the most likely genre.
    prediction = genre_model.predict(input_vector)[0]
    probabilities = genre_model.predict_proba(input_vector)[0]

    print("\nPredicted genre:", prediction)
    print("\nOther genre estimates:")

    # Show the three highest model probability estimates.
    ranked = np.argsort(probabilities)[::-1][:3]

    for i in ranked:
        print(
            f"{genre_model.classes_[i]}: "
            f"{probabilities[i]:.2%}"
        )


# ============================================================
# SECTION 9: EXPLORE THE DATASET
# Show statistics, genre counts and missing values.
# ============================================================

def explore_dataset():
    print("\n========== DATASET EXPLORATION ==========")

    print("Total books:", len(df))
    print("Unique authors:", df["Author"].nunique())
    print("Unique genres:", df["Genre"].nunique())

    if df["Year"].notna().any():
        print("Oldest publication year:", int(df["Year"].min()))
        print("Newest publication year:", int(df["Year"].max()))
    else:
        print("Publication years are unavailable.")

    if df["Rating"].notna().any():
        print(f"Average rating: {df['Rating'].mean():.2f}")
    else:
        print("Ratings are unavailable.")

    print("\nBooks per genre:")
    print(df["Genre"].value_counts().to_string())

    print("\nMissing values in the original CSV:")
    print(original_missing.to_string())

    print("\nNumerical summary:")
    print(df[["Year", "Rating"]].describe().round(2).to_string())


# ============================================================
# SECTION 10: DATA VISUALIZATIONS
# Six separate graphs demonstrate different aspects of the data.
# ============================================================

def plot_genre_distribution():
    # Graph 1: Pie chart showing genre proportions.
    counts = df["Genre"].value_counts()

    plt.figure(figsize=(8, 8))
    plt.pie(counts.values, labels=counts.index, autopct="%1.1f%%")
    plt.title("Distribution of Books by Genre")
    plt.tight_layout()
    plt.show()


def plot_books_by_genre():
    # Graph 2: Bar graph comparing the number of books per genre.
    counts = df["Genre"].value_counts()

    plt.figure(figsize=(10, 5))
    plt.bar(counts.index, counts.values)
    plt.title("Number of Books per Genre")
    plt.xlabel("Genre")
    plt.ylabel("Number of Books")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.show()


def plot_publication_trend():
    # Graph 3: Line graph showing publication-year counts.
    years = df["Year"].dropna().astype(int)

    if years.empty:
        print("No publication years are available.")
        return

    counts = years.value_counts().sort_index()

    plt.figure(figsize=(10, 5))
    plt.plot(counts.index, counts.values, marker="o")
    plt.title("Book Publication Year Trend")
    plt.xlabel("Publication Year")
    plt.ylabel("Number of Books")
    plt.tight_layout()
    plt.show()


def plot_rating_distribution():
    # Graph 4: Histogram showing the distribution of ratings.
    ratings = df["Rating"].dropna()

    if ratings.empty:
        print("No ratings are available.")
        return

    plt.figure(figsize=(8, 5))
    plt.hist(ratings, bins=10)
    plt.title("Distribution of Book Ratings")
    plt.xlabel("Rating")
    plt.ylabel("Number of Books")
    plt.tight_layout()
    plt.show()


def plot_recommendation_scores():
    # Graph 5: Compare scores from the latest recommendation.
    if last_recommendations.empty:
        print("First use 'Recommend Similar Books'.")
        return

    plt.figure(figsize=(10, 5))
    plt.bar(
        last_recommendations["Title"],
        last_recommendations["Similarity"]
    )
    plt.title("Recommendation Similarity Scores")
    plt.xlabel("Recommended Books")
    plt.ylabel("Cosine Similarity")
    plt.xticks(rotation=35, ha="right")
    plt.tight_layout()
    plt.show()


def plot_confusion_matrix():
    # Graph 6: Compare actual and predicted genres.
    if not genre_model_ready:
        print("The genre model is not ready.")
        return

    labels = genre_model.classes_

    plt.figure(figsize=(9, 7))
    plt.imshow(confusion, interpolation="nearest")
    plt.title("Genre Prediction Confusion Matrix")
    plt.xlabel("Predicted Genre")
    plt.ylabel("Actual Genre")

    positions = np.arange(len(labels))
    plt.xticks(positions, labels, rotation=45, ha="right")
    plt.yticks(positions, labels)

    # Write the number of predictions inside each cell.
    for row in range(confusion.shape[0]):
        for col in range(confusion.shape[1]):
            plt.text(
                col, row, str(confusion[row, col]),
                ha="center", va="center"
            )

    plt.tight_layout()
    plt.show()


def visualizations_menu():
    # Let the user choose which graph to display.
    while True:
        print("\n========== DATA VISUALIZATIONS ==========")
        print("1. Genre Distribution - Pie Chart")
        print("2. Books per Genre - Bar Graph")
        print("3. Publication Year Trend - Line Graph")
        print("4. Rating Distribution - Histogram")
        print("5. Recommendation Similarity Scores")
        print("6. Confusion Matrix")
        print("7. Back to Main Menu")

        choice = input("Choose a graph: ").strip()

        if choice == "1":
            plot_genre_distribution()
        elif choice == "2":
            plot_books_by_genre()
        elif choice == "3":
            plot_publication_trend()
        elif choice == "4":
            plot_rating_distribution()
        elif choice == "5":
            plot_recommendation_scores()
        elif choice == "6":
            plot_confusion_matrix()
        elif choice == "7":
            break
        else:
            print("Invalid choice. Enter a number from 1 to 7.")


# ============================================================
# SECTION 11: MODEL PERFORMANCE
# Display the actual test accuracy and confusion matrix.
# ============================================================

def model_performance():
    print("\n========== MODEL PERFORMANCE ==========")

    if not genre_model_ready:
        print("The genre model could not be trained.")
        print("Collect more examples for each genre.")
        return

    print("Algorithm: Multinomial Naive Bayes")
    print("Feature extraction: TF-IDF")
    print("Training samples:", X_train.shape[0])
    print("Testing samples:", X_test.shape[0])
    print(f"Test accuracy: {genre_accuracy:.2%}")

    print("\nGenre labels:")
    print(list(genre_model.classes_))

    print("\nConfusion matrix:")
    print(confusion)

    print("\nAccuracy is measured on held-out test data.")
    print("It may change with the dataset and its quality.")


# ============================================================
# SECTION 12: MAIN MENU
# Keep showing the menu until the user selects Exit.
# ============================================================

def main():
    while True:
        print("\n")
        print("=" * 44)
        print("              BOOKVERSERA")
        print("        AI BOOK DISCOVERY SYSTEM")
        print("=" * 44)
        print("1. Display Books")
        print("2. Search Books")
        print("3. Recommend Similar Books")
        print("4. Predict Book Genre")
        print("5. Explore Dataset")
        print("6. Data Visualizations")
        print("7. Model Performance")
        print("8. Exit")
        print("=" * 44)

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            display_books()
        elif choice == "2":
            search_books()
        elif choice == "3":
            recommend_books()
        elif choice == "4":
            predict_genre()
        elif choice == "5":
            explore_dataset()
        elif choice == "6":
            visualizations_menu()
        elif choice == "7":
            model_performance()
        elif choice == "8":
            print("\nThank you for using BookVersera!")
            print("Happy reading!")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 8.")


# ============================================================
# SECTION 13: START THE PROGRAM
# Execute the menu when this file is run directly.
# ============================================================

if __name__ == "__main__":
    main()
