<template>
  <div class="container-fluid p-1">
    <h3>Job <img src="favicon.ico" width="7%">Toise</h3>

    <div class="btn-group">
      <button class="btn btn-primary" :class="{ active: activeTab == 0 }" @click="activeTab = 0">Search</button>
      <button class="btn btn-primary" :class="{ active: activeTab == 1 }" @click="activeTab = 1">Seen</button>
      <button class="btn btn-primary" :class="{ active: activeTab == 2 }" @click="activeTab = 2">Liked</button>
      <button class="btn btn-primary" :class="{ active: activeTab == 3 }" @click="activeTab = 3">Disliked</button>
    </div>

    <form v-if="activeTab == 0" @submit.prevent="searchJobs" class="row g-3 align-items-center">
      <!-- Keyword Input -->
      <div class="col-auto">
        <label for="keyword" class="form-label">Keyword</label>
        <input type="text" id="keyword" v-model="queryOptions.keyword" class="form-control"
          placeholder="Enter keyword" />
      </div>

      <!-- Location Input -->
      <div class="col-auto">
        <label for="location" class="form-label">Location</label>
        <input type="text" id="location" v-model="queryOptions.location" class="form-control"
          placeholder="Enter location" />
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
    <JobTable :jobData="jobData"></JobTable>
  </div>
</template>

<script>
//import { getFunctions, httpsCallable } from "firebase/functions";
import JobTable from './JobTable.vue';
import jobStore from '@/store/index';

export default {
  components: { JobTable },
  setup() {
    const jStore = jobStore();
    return { jStore }
  },
  data() {
    return {
      searchResults: [],
      queryOptions: {
        keyword: 'AI',
        location: 'Spain',
        dateSincePosted: '',
        jobType: '',
        remoteFilter: 'remote',
        salary: '',
        experienceLevel: '',
        limit: '5',
        page: 0,
        sortBy: 'relevant'
      },
      activeTab: 0
    }
  },
  computed: {
    jobData() {
      let res;
      switch (this.activeTab) {
        case 0:
          res = this.searchResults;
          break;
        case 1:
          res = this.jStore.seenJobs;
          break;
        case 2:
          res = this.jStore.likedJobs;
          break;
        case 3:
          res = this.jStore.dislikedJobs;
          break;
      }
      return res
    }
  },
  methods: {
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

      const serverResp = await liAPI(this.queryOptions);
      console.log(serverResp)
      this.searchResults = this.jStore.addJobs(serverResp);
    }
  },
  mounted() {
    this.jStore.loadAll()
      .then(() => {
        console.log(this.jStore.jobList)
      })
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
