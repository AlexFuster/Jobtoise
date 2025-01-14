<template>
  <div class="container-fluid p-2 mt-4">
    <h3>Job Table</h3>
    <form @submit.prevent="searchJobs" class="row g-3 align-items-center mb-3">
      <!-- Keyword Input -->
      <div class="col-auto">
        <label for="keyword" class="form-label">Keyword</label>
        <input type="text" id="keyword" v-model="queryOptions.keyword" class="form-control" placeholder="Enter keyword" />
      </div>

      <!-- Location Input -->
      <div class="col-auto">
        <label for="location" class="form-label">Location</label>
        <input type="text" id="location" v-model="queryOptions.location" class="form-control" placeholder="Enter location" />
      </div>

      <!-- Remote Filter Dropdown -->
      <div class="col-auto">
        <label for="remoteFilter" class="form-label">Work Type</label>
        <select id="remoteFilter" v-model="queryOptions.remoteFilter" class="form-select">
          <option value="on site">On Site</option>
          <option value="remote">Remote</option>
          <option value="hybrid">Hybrid</option>
        </select>
      </div>

      <!-- Submit Button -->
      <div class="col-auto">
        <button type="submit" class="btn btn-primary mt-4">Search</button>
      </div>
    </form>

    <table class="table table-bordered">
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
                    <td><a :href="position.jobUrl">{{ position.position }}</a></td>
                    <td>{{ position.location }}</td>
                    <td>{{ position.date }}</td>
                    <td>{{ position.Salary }}</td>
                    <td>{{ position.Role }}</td>
                    <td>{{ position.Technologies }}</td>
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
//import { getFunctions, httpsCallable } from "firebase/functions";
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
      groupedJobData: [],
      queryOptions:{
        keyword: 'AI',
        location: 'Spain',
        dateSincePosted: '',
        jobType: '',
        remoteFilter: 'remote',
        salary: '',
        experienceLevel: '',
        limit: '5',
        page: "1",
        sortBy: 'relevant'
      }
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
    async searchJobs() {
      /*const functions = getFunctions();
      const liAPI = httpsCallable(functions, 'searchLI');*/

      const liAPI = async (queryOptions) => {
        const resp = await fetch('http://localhost:3000/searchLI',
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ queryOptions: queryOptions })
          }
        );
        const data = await resp.json();
        return data;
      }

      const gcloudResp = await liAPI(this.queryOptions);
      console.log(gcloudResp)
      this.jobData = gcloudResp.data;
      this.groupedJobData = this.getGroupedJobData();
    }
  },
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
