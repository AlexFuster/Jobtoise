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
                  <div v-for="(message, index) in messages" :key="index" class="mb-2">
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
      messages: [
        { sender: 'Bot', text: 'Hello! How can I assist you today?' },
      ],
      userInput: '',
    };
  },
  props:['contextTitle'],
  methods: {
    toggleChat() {
      console.log(this.contextTitle)
      this.isOpen = !this.isOpen;
    },
    sendMessage() {
      if (this.userInput.trim() !== '') {
        this.messages.push({ sender: 'You', text: this.userInput });
        this.userInput = '';

        // Simulate bot response
        setTimeout(() => {
            this.messages.push({ sender: 'Bot', text: 'Thank you for your message!' });
        }, 1000);
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