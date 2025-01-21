import { defineStore } from 'pinia'

class Job {
  constructor(loadedJob) {
    Object.assign(this, loadedJob);
  }
  async likeJob() {
    await fetch('http://localhost:3000/likeJob',
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company: this.company, position: this.position, like: !this.liked })
      }
    )
    this.liked = !this.liked;
    this.disliked = false;
  }
  async dislikeJob() {
    await fetch('http://localhost:3000/dislikeJob',
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company: this.company, position: this.position, dislike: !this.disliked })
      }
    )
    this.liked = false;
    this.disliked = !this.disliked
  }
}

export default defineStore('jobs', {
  state() {
    return {
      jobList: []
    }
  },
  getters: {
    likedJobs(state) { return state.jobList.filter((job) => job.liked) },
    dislikedJobs(state) { return state.jobList.filter((job) => job.disliked) },
    seenJobs(state) { return state.jobList.filter((job) => !job.liked && !job.disliked) }
  },
  actions: {
    async loadAll() {
      this.jobList = [];
      return fetch('http://localhost:3000/loadAll')
        .then(resp => resp.json())
        .then(jsonData => {
          this.addJobs(jsonData);
        })
        .catch(error => { console.log(error) })
    },
    addJobs(jsonData) {
      let addedJobs = [];
      jsonData.data.forEach(element => {
        const job = new Job(element);
        this.jobList.push(job);
        addedJobs.push(job)
      });
      return addedJobs;
    }
  }
})
