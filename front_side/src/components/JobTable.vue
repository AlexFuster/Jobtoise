<template>
  <div>
    <ChatbotWindow ref="chatbot" :contextTitle="contextTitle"></ChatbotWindow>
    <table class="table table-bordered mt-3">
      <thead>
        <tr>
          <th>Company</th>
          <th>Mission</th>
          <th>Business model</th>
          <th>Size (Employees)</th>
          <th>Age (Years)</th>
          <th>Maturity level</th>
        </tr>
      </thead>
      <tbody>
        <template v-for="(companyGroup, companyIndex) in groupedJobData" :key="companyIndex">
          <!-- Company Row -->
          <tr>
            <td>
              <button class="btn btn-link text-start w-100" @click="companyGroup.collapsed = !companyGroup.collapsed">
                <img :src="companyGroup.companyLogo" class="me-2">
                {{ companyGroup.company }} ({{ companyGroup.positions.length }} positions)
              </button>
            </td>
            <td>{{ companyGroup.mission }}</td>
            <td>{{ companyGroup.revenue }}</td>
            <td>{{ companyGroup.size }}</td>
            <td>{{ companyGroup.age }}</td>
            <td>{{ companyGroup.maturity }}</td>
          </tr>
          <!-- Positions Rows -->
          <tr :class="{ collapse: companyGroup.collapsed }">
            <td colspan="6">
              <table class="table table-borderless">
                <thead>
                  <tr>
                    <th>Position</th>
                    <th>Location</th>
                    <th>Date</th>
                    <th>Salary</th>
                    <th>Role Description</th>
                    <th>Requirements</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(position, positionIndex) in companyGroup.positions" :key="positionIndex">
                    <td class="align-middle"><a :href="position.jobUrl">{{ position.position }}</a></td>
                    <td class="align-middle">{{ position.location }}</td>
                    <td class="align-middle">{{ position.date }}</td>
                    <td class="align-middle">{{ position.Salary }}</td>
                    <td class="align-middle">{{ position.Role }}</td>
                    <td class="align-middle">{{ position.Technologies }}</td>
                    <td class="align-middle">
                      <div class="d-flex flex-row justify-content-center">
                        <i class="btn btn-primary bi fs-4 rounded-start-5 rounded-0"
                          :class="position.liked ? 'bi-hand-thumbs-up-fill' : 'bi-hand-thumbs-up'"
                          @click="likeJob(position)"></i>

                        <i class="btn btn-primary bi fs-4 rounded-0"
                          :class="position.disliked ? 'bi-hand-thumbs-down-fill' : 'bi-hand-thumbs-down'"
                          @click="dislikeJob(position)"></i>
                        <button class="btn btn-primary rounded-end-5  bi bi-robot fs-4 rounded-0"
                          @click="openChatbot(companyGroup.company, position.position)"></button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
</template>

<script>
import jobStore from '@/store/index';
import ChatbotWindow from './ChatbotWindow.vue';

export default {
  setup(){
    const jStore = jobStore();
    return {jStore}
  },
  props: {
    jobData: {
      type: Array,
      required: true,
    },
  },
  components:{ChatbotWindow},
  data() {
    return {
      groupedJobData: [],
      isHoveredUp: false,
      isHoveredDown: false,
      contextTitle:''
    }
  },
  methods: {
    getGroupedJobData() {
      return this.jobData.reduce((acc, job) => {
        const companyIndex = acc.findIndex(item => item.company === job.company);
        if (companyIndex === -1) {
          acc.push({
            company: job.company,
            companyLogo: job.companyLogo,
            mission: job.Mission,
            revenue: job.Revenue,
            size: job.Size,
            age: job.Age,
            maturity: job.Maturity,
            collapsed: false,
            positions: [job]
          });
        } else {
          acc[companyIndex].positions.push(job);
        }
        return acc;
      }, []);
    },
    openChatbot(company,position){
      this.contextTitle = JSON.stringify({company,position})
      this.$refs.chatbot.toggleChat();
    },
    likeJob(job) {
      job.likeJob()
    },
    dislikeJob(job) {
      job.dislikeJob();
    }
  },
  watch: {
    jobData() {
      this.groupedJobData = this.getGroupedJobData();
    }
  }
}
</script>