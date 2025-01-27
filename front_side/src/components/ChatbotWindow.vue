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
                  <div v-for="(message, index) in messages[contextTitle]" :key="index" class="mb-2">
                      <strong>{{ message.sender }}:</strong> {{ message.text }}
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
export default {
  data() {
    return {
      isOpen: false,
      messages:{},
      userInput: '',
      company:'',
      position:''
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
      console.log(this.contextTitle)
      if(!this.isOpen){
        this.openChat()
      }else{
        this.isOpen = false;
      }
    },
    openChat(company, position){
      if(company && position){
        this.company = company;
        this.position = position
      }
      if(!this.messages[this.contextTitle]){
        this.messages[this.contextTitle] = [{ sender: 'Bot', text: 'Hello! How can I assist you today?' }]
      }
      console.log(this.contextTitle,this.messages,this.messages[this.contextTitle])
      this.isOpen = true;
    },
    async sendMessage() {
      if (this.userInput.trim() !== '') {
        this.messages[this.contextTitle].push({ sender: 'You', text: this.userInput });
        const query = this.userInput
        this.userInput = '';

        const resp = await fetch('http://localhost:3000/askBot',
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              query: query,
              company: this.company,
              position: this.position
            })
          }
        );
        const jsonData = await resp.json();
        this.messages[this.contextTitle].push({sender: 'Bot', text: jsonData.data.answer})
      }
    },
    scrollToBottom() {
        const chatBody = this.$refs.chatBody;
        if (chatBody) {
            chatBody.scrollTop = chatBody.scrollHeight;
        }
    },
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