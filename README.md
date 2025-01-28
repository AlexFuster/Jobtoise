# jobtoise

<img src="./front_side/public/jobtoise.jpeg" width="105"/>

### WIP

AI powered LinkedIn Job search Page.
It uses LLMs to organize, summarize and retrieve information about job offers.
The page is intended only for local use, as it uses LinkedIn guest web scrapping, and not the official API, which is private.

The app is not yet very intuitive, as it is yet in development.

Here we have a video that shows the main functionality:
[![Jobtoise video](https://i9.ytimg.com/vi_webp/A7V84hYfp_k/maxresdefault.webp?v=67987db8&sqp=COz54bwG&rs=AOn4CLBEXgmWbTBOwNL0qXZIr7f92-USrA)](https://youtu.be/A7V84hYfp_k)


Here it is the intended worflow of the app:

1. Go to the "Search" tab, add your search filters and click the "search" button
2. The retrieved offers are processed by ChatGPT in order to summarize them and return them in an structured format. The outputs of this process are shown in a table. They are grouped by company and can be collapsed.
3. The offers have been saved to the MongoDB database. You can see the saved offers in the "Seen" tab.
4. In order to increase your number of saved offers, you can search again. The search process will not return offers that you already have saved.
5. You can classify job offers by liking (👍) or disliking (👎) them. The offers will get moved to the corresponding tab ("Liked" or "Disliked") and disapear from the other tabs to avoid duplication
6. You can click the chatbot button (🤖) in one of the rows of the list. The chatbot automatically receives the full context of the offer. It will load (if any) past conversations about that offer. 
7. Instead of asking questions about a specific offer, you can use the big "🤖 Open chatbot assistant" button on top of the table. It will open a chat with no initial context (unless there are previous conversations to load). You can ask it to "search" or "find" jobs that correspond with the criteria you define. It will perform a RAG search in Qdrant over the saved offers and automatically retrieve the offers, whose context is then used. For atomicity, further searches invalidate previous ones.

## Setup
The easiest way to set it up is through docker compose
You need to have docker and docker compose installed in your machine.
1. Add your OpenAI API key to the environment variable in ```docker-compose.yaml```
2. Build containers: ```docker compose build```
3. Run containers: ```docker compose up```

## TODO
* Include more boards appart from LinkedIn
* Upload your CV and embed it in order to do semantic search with it (eg. search the jobs that better match my profile)

