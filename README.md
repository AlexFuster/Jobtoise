# jobtoise

<img src="./front_side/public/jobtoise.jpeg" width="105"/>

### WIP

AI powered LinkedIn Job search Page.
It uses chatGPT to organize and summarize information about offers.
The page is intended only for local us, as it uses LinkedIn guest web scrapping, and not the official API, which is private.

## Manual setup

### Frontend setup
You need to have node installed in your machine.
1. ```cd front_side```
2. Install dependencies: ```npm install```
3. serve the page locally: ```npm run serve```

### DB setup
You can skip this if you already have mongoDB installed in your machine.
```
sudo apt update
sudo apt install -y mongodb
sudo systemctl start mongodb
sudo systemctl enable mongodb
```

### Backend setup
You need to have Python3 installed in your machine.
1. ```cd server_fastapi```
2. Add OpenAI API key: ```echo "apiKey = '$YOUR_API_KEY'">mykeys.py```
3. Install dependencies: 
```
python -m venv pyenv
source pyenv/bin/activate
pip install -r requirements.txt
```
4. Run server: ```fastapi dev```

## Docker-compose setup
You need to have docker and docker compose installed in your machine.
1. Add OpenAI API key: ```echo "apiKey = '$YOUR_API_KEY'">server_fastapi/mykeys.py```
2. Build containers: ```docker compose build```
3. Run containers: ```docker compose up```


