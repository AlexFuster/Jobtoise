import requests
from bs4 import BeautifulSoup
from random import uniform
import time
from datetime import datetime, timedelta


# Utility function for delay
def delay(seconds):
    time.sleep(seconds)


# Cache implementation
class JobCache:
    def __init__(self):
        self.cache = {}
        self.TTL = 60 * 60  # 1 hour

    def set(self, key, value):
        self.cache[key] = {"data": value, "timestamp": datetime.now()}

    def get(self, key):
        item = self.cache.get(key)
        if not item:
            return None
        if (datetime.now() - item["timestamp"]).total_seconds() > self.TTL:
            del self.cache[key]
            return None
        return item["data"]

    def clear(self):
        now = datetime.now()
        keys_to_remove = [
            key
            for key, value in self.cache.items()
            if (now - value["timestamp"]).total_seconds() > self.TTL
        ]
        for key in keys_to_remove:
            del self.cache[key]


cache = JobCache()


# Main query function
class Query:
    def __init__(self, query_obj):
        self.host = query_obj.get("host", "www.linkedin.com")
        self.keyword = query_obj.get("keyword", "").strip().replace(" ", "+")
        self.location = query_obj.get("location", "").strip().replace(" ", "+")
        self.date_since_posted = query_obj.get("dateSincePosted", "")
        self.job_type = query_obj.get("jobType", "")
        self.remote_filter = query_obj.get("remoteFilter", "")
        self.salary = query_obj.get("salary", "")
        self.experience_level = query_obj.get("experienceLevel", "")
        self.sort_by = query_obj.get("sortBy", "")
        self.limit = int(query_obj.get("limit", 0))
        self.page = int(query_obj.get("page", 0))

    def get_date_since_posted(self):
        date_range = {
            "past month": "r2592000",
            "past week": "r604800",
            "24hr": "r86400",
        }
        return date_range.get(self.date_since_posted.lower(), "")

    def get_experience_level(self):
        experience_range = {
            "internship": "1",
            "entry level": "2",
            "associate": "3",
            "senior": "4",
            "director": "5",
            "executive": "6",
        }
        return experience_range.get(self.experience_level.lower(), "")

    def get_job_type(self):
        job_type_range = {
            "full time": "F",
            "part time": "P",
            "contract": "C",
            "temporary": "T",
            "volunteer": "V",
            "internship": "I",
        }
        return job_type_range.get(self.job_type.lower(), "")

    def get_remote_filter(self):
        remote_filter_range = {
            "on-site": "1",
            "remote": "2",
            "hybrid": "3",
        }
        return remote_filter_range.get(self.remote_filter.lower(), "")

    def get_salary(self):
        salary_range = {
            "40000": "1",
            "60000": "2",
            "80000": "3",
            "100000": "4",
            "120000": "5",
        }
        return salary_range.get(self.salary, "")

    def get_page(self):
        return self.page * 25

    def url(self, start):
        query = f"https://{self.host}/jobs-guest/jobs/api/seeMoreJobPostings/search?"
        params = {
            "keywords": self.keyword,
            "location": self.location,
            "f_TPR": self.get_date_since_posted(),
            "f_SB2": self.get_salary(),
            "f_E": self.get_experience_level(),
            "f_WT": self.get_remote_filter(),
            "f_JT": self.get_job_type(),
            "start": start + self.get_page(),
        }
        if self.sort_by == "recent":
            params["sortBy"] = "DD"
        elif self.sort_by == "relevant":
            params["sortBy"] = "R"
        return query + "&".join(f"{k}={v}" for k, v in params.items() if v)

    def fetch_jobs(self):
        all_jobs = []
        start = 0
        batch_size = 25
        has_more = True
        consecutive_errors = 0
        max_consecutive_errors = 3

        cache_key = self.url(0)
        cached_jobs = cache.get(cache_key)
        if cached_jobs:
            print("Returning cached results")
            return cached_jobs

        while has_more:
            try:
                jobs = self.fetch_job_batch(start)
                if not jobs:
                    has_more = False
                    break

                all_jobs.extend(jobs)
                print(f"Fetched {len(jobs)} jobs. Total: {len(all_jobs)}")

                if self.limit and len(all_jobs) >= self.limit:
                    all_jobs = all_jobs[: self.limit]
                    break

                consecutive_errors = 0
                start += batch_size
                delay(2 + uniform(0, 1))
            except Exception as e:
                consecutive_errors += 1
                print(f"Error fetching batch (attempt {consecutive_errors}): {e}")

                if consecutive_errors >= max_consecutive_errors:
                    print("Max consecutive errors reached. Stopping.")
                    break

                delay(2**consecutive_errors)

        if all_jobs:
            cache.set(cache_key, all_jobs)

        return all_jobs

    def fetch_job_batch(self, start):
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://www.linkedin.com/jobs",
        }

        response = requests.get(self.url(start), headers=headers, timeout=10)
        if response.status_code == 429:
            raise Exception("Rate limit reached")
        response.raise_for_status()

        return self.parse_job_list(response.text)

    @staticmethod
    def parse_job_list(job_data):
        soup = BeautifulSoup(job_data, "html.parser")
        jobs = []

        for job in soup.find_all("li"):
            try:
                position = job.select_one(".base-search-card__title").text.strip()
                company = job.select_one(".base-search-card__subtitle").text.strip()
                location = job.select_one(".job-search-card__location").text.strip()
                date = job.select_one("time")["datetime"]
                salary = job.select_one(".job-search-card__salary-info")
                salary = (
                    salary.text.strip().replace("\s+", " ")
                    if salary
                    else "Not specified"
                )
                jobUrl = job.select_one(".base-card__full-link")["href"]
                companyLogo = job.select_one(".artdeco-entity-image")[
                    "data-delayed-url"
                ]
                agoTime = job.select_one(".job-search-card__listdate")
                agoTime = agoTime.text.strip() if agoTime else ""

                if position and company:
                    jobs.append(
                        {
                            "position": position,
                            "company": company,
                            "location": location,
                            "date": date,
                            "salary": salary,
                            "jobUrl": jobUrl,
                            "companyLogo": companyLogo,
                            "agoTime": agoTime,
                        }
                    )
            except Exception as e:
                print(f"Error parsing job: {e}")

        return jobs


def query(query_obj):
    query = Query(query_obj)
    jobs = query.fetch_jobs()
    return jobs


# Example usage
if __name__ == "__main__":
    query_obj = {
        "keyword": "Software Engineer",
        "location": "San Francisco",
        "limit": 50,
    }
    print(query(query_obj))