<template>
    <div class="fixed-bottom w-25 zindex-1">
        <div class="card">
            <div
                class="card-header chatbot-header d-flex justify-content-between align-items-center"
                @click="toggleChat"
            >
                <span>Chatbot Assistant</span>
                <button class="btn btn-sm btn-light">{{ isOpen ? '-' : '+' }}</button>
            </div>
            <div v-if="isOpen" class="card-body overflow-y-scroll d-flex flex-column justify-content-between" style="height: 50vh;" ref="chatBody">
                <div>
                  <em v-if="contextTitle">Context taken from {{ contextTitle }}</em>
                  <div v-for="(message, index) in messages" :key="index" class="mb-2 d-flex flex-row " :class="message.sender==='Bot' ? 'text-start justify-content-start' : 'text-end justify-content-end'">
                      <div class="w-75 border border-primary rounded-4 p-3">
                        <strong>{{ message.sender }}:</strong> 
                        <div v-html="markdown2Html(message.text)"></div>
                        <!--{{ message.text }}-->
                      </div>
                  </div>
                </div>
                <div class="input-group">
                    <input
                        type="text"
                        class="form-control"
                        v-model="userInput"
                        @keyup.enter="sendMessage"
                        placeholder="Type a message..."
                    />
                    <button class="btn btn-primary" @click="sendMessage">Send</button>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { marked } from "marked";
export default {
  data() {
    return {
      isOpen: false,
      messages:[],
      userInput: '',
      company:null,
      position:null
    };
  },
  computed:{
    contextTitle(){
      if(!this.company || !this.position)
        return 'global'
      
      return JSON.stringify({company: this.company, position: this.position})
    }
  },
  methods: {
    toggleChat() {
      if(!this.isOpen){
        this.openChat(this.company, this.position)
      }else{
        this.isOpen = false;
      }
    },
    async openChat(company, position){
      if(company!=this.company || position!=this.position){
        this.company = company;
        this.position = position
        const resp = await fetch('http://localhost:3000/openConversation',
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              company: this.company,
              position: this.position
            })
          }
        );
        const jsonData = await resp.json();
        this.messages = [{ sender: 'Bot', text: 'Hello! How can I assist you today?' }]
        this.messages.push(...jsonData.messages)
      }
      this.isOpen = true;
    },
    async sendMessage() {
      if (this.userInput.trim() !== '') {
        this.messages.push({ sender: 'You', text: this.userInput });
        const query = this.userInput
        this.userInput = '';

        const resp = await fetch('http://localhost:3000/askBot',
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({query: query})
          }
        );
        const jsonData = await resp.json();
        this.messages.push({sender: 'Bot', text: jsonData.data.answer})
      }
    },
    scrollToBottom() {
        const chatBody = this.$refs.chatBody;
        if (chatBody) {
            chatBody.scrollTop = chatBody.scrollHeight;
        }
    },
    markdown2Html(md){
      return marked(md)
    }
  },
  updated() {
    this.$nextTick(() => {
      this.scrollToBottom();
    });
  },
}
</script>

<style scoped>
  .chatbot-header {
      cursor: pointer;
  }
</style>