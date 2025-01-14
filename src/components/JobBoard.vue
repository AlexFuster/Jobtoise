<template>
  <div class="container-fluid p-2 mt-4">
    <h3>Job Table</h3>
    <button @click="searchJobs" class="btn btn-primary">Search</button>

    <table class="table table-bordered">
      <thead>
        <tr>
          <th>Company</th>
          <th>Mission</th>
          <th>Business model</th>
          <th>Size</th>
          <th>Age</th>
          <th>Maturity</th>
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
            <td>aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa</td>
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
                    <td><a :href="position.jobUrl">{{ position.position }}</a></td>
                    <td>{{ position.location }}</td>
                    <td>{{ position.date }}</td>
                    <td>{{ position.salary }}</td>
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
import { getFunctions, httpsCallable } from "firebase/functions";
import OpenAI from "openai";
export default {
  props: {
    columns: {
      type: Array,
      required: true,
    },
  },
  data() {
    return {
      jobData: [],
      groupedJobData: []
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
            collapsed: false,
            positions: [job]
          });
        } else {
          acc[companyIndex].positions.push(job);
        }
        return acc;
      }, []);
    },
    async searchJobs() {
      const queryOptions = {
        keyword: 'AI',
        location: 'Spain',
        dateSincePosted: '',
        jobType: '',
        remoteFilter: 'remote',
        salary: '',
        experienceLevel: '',
        limit: '10',
        page: "0",
        sortBy: 'relevant'
      };
      const functions = getFunctions();
      const liAPI = httpsCallable(functions, 'searchLI');
      const gcloudResp = await liAPI(queryOptions);
      console.log(gcloudResp)
      this.jobData = gcloudResp.data;
      this.groupedJobData = this.getGroupedJobData();
    }
  },
  mounted() {
    

  }
};
</script>

<style scoped>
table.table td {
  vertical-align: middle;
}

.collapse {
  transition: none !important;
}
</style>
