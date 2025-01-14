const express = require('express');
const cors = require('cors');
const linkedIn = require('linkedin-jobs-api');
const OpenAI = require("openai");
const cheerio = require('cheerio');
const z = require('zod')
const crypto = require('crypto');
const { zodResponseFormat } = require('openai/helpers/zod')
const { initializeApp } = require("firebase/app");
const  { getDatabase, ref, get, set, push, remove, update } = require("firebase/database");
const firebaseConfig = require('./firebaseConf')

initializeApp(firebaseConfig);
const db = getDatabase();
var offers = {}
get(ref(db, '/')).then((snapshot) => {
  if (snapshot.exists()) {
    offers = snapshot.val();
  }
})

const apiKey = 'XXXX'

const OutFormat = z.object({
  Mission: z.string(),
  Revenue: z.string(),
  Size: z.array(z.number()),
  Age: z.number(),
  Maturity: z.string(),
  Role: z.string(),
  Technologies: z.string(),
  Salary: z.string()
});

function getCompanyPrompt(company, context) {
  return `Summarize the following information about a job offer of the company ${company} and return it in JSON format.
  A sentence with the mission (Avoid vague marketing expressions)
  Revenue type (public, product(B2C), product(B2B) consultancy)
  Company size in aproximated number of employees (just the range)
  Company aproximated age in years
  Company maturity: one of startup(low revenue, fully deppends on investment), scaleup(sustainable revenue, gets help from investment), consolidated(high revenue, does not need investment))
  Very brief description of the role
  Key technologies and knowledge fields that they require (as a succession of keywords)
  Salary range if available (else, not specified)

  Example output with a Google offer:

  {
    "Mission": "It is a search engine that indexes and serves web pages.",
    "Revenue": "Product(B2C)",
    "Size": [150000, 200000],
    "Age": "27",
    "Maturity": "Consolidated",
    "Role": "Develop and optimize deep learning models for image generation",
    "Technologies": "Deep learning, Pytorch, Diffusion models, model optimization"
    "Salary": "120000$-150000$"
  }

  Here is some context of the offer:
  ${context}
  `
}

async function fetchWithRetry(url, retries = 3, delayMs = 2000) {
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      if (attempt > 1)
        console.log(`Attempt ${attempt} to fetch ${url}`);
      const resp = await fetch(url);
      const html = await resp.text();

      const $ = cheerio.load(html);
      const description = $('div.show-more-less-html__markup.show-more-less-html__markup--clamp-after-5').first().html();
      const jsonContent = $('script[type="application/ld+json"]').first().html()
      const salary = $('div.salary.compensation__salary').first().html()

      let context = description
      if (jsonContent) {
        const jsonData = JSON.parse(jsonContent);
        if (jsonData.baseSalary)
          context += '\nbaseSalary:' + JSON.stringify(jsonData.baseSalary)
      } else if (salary) {
        context += '\nsalary:' + salary;
      }

      if (context)
        return context

      console.warn(`Attempt ${attempt} failed: context is null.`);
    } catch (error) {
      console.error(`Attempt ${attempt} failed with error:`, error);
    }

    // Wait before retrying
    if (attempt < retries) {
      await new Promise(resolve => setTimeout(resolve, Math.random() * delayMs + 1000));
    }
  }

  return null
};

const app = express();
const port = 3000;

app.use(cors({
  origin: '*', // Allow all origins
  methods: ['POST'], // Allow these HTTP methods
  allowedHeaders: ['Content-Type'], // Allow these headers
}));

// Middleware to parse JSON
app.use(express.json());

function generateHash(company, position) {
  const hash = crypto.createHash('sha256');
  hash.update(company + position);
  return hash.digest('hex');  // Generates a hash string that is safe for Firebase paths
}

// Define a simple endpoint
app.post('/searchLI', async (request, response) => {
  const { queryOptions } = request.body;
  console.log(queryOptions)
  let emptyResults = true
  let nonDupData = {}
  while (emptyResults && queryOptions.page<10) {
    const data = await linkedIn.query(queryOptions)
    data.forEach(element => {
      const uniqueKey = generateHash(element.company,element.position);

      if (!(uniqueKey in offers || uniqueKey in nonDupData)) {
        nonDupData[uniqueKey] = element;
      }
    })
    emptyResults =  Object.keys(nonDupData).length===0
    queryOptions.page++;
  }

  let gptProms = [];
  const openai = new OpenAI({ apiKey: apiKey });
  let retData = [];

  for (let uniqueKey in nonDupData) {
    let element = nonDupData[uniqueKey];
    console.log(element)
    gptProms.push(fetchWithRetry(element.jobUrl)
      .then((context) => {
        if (context) {
          const completion = openai.chat.completions.create({
            model: "gpt-4o-mini",
            store: true,
            messages: [
              { "role": "user", "content": getCompanyPrompt(element.company, context) },
            ],
            response_format: zodResponseFormat(OutFormat, "offers")
          });

          completion.then((result) => {
            const msg = JSON.parse(result.choices[0].message.content);
            Object.assign(element, msg);
            retData.push(element);
            set(ref(db, '/' + uniqueKey), element);
            offers[uniqueKey] = element;
          });
          return completion
        } else {
          return new Promise(resolve => resolve());
        }
      }))
  };
  Promise.all(gptProms).then(() => {
    console.log('Finished')
    response.send({ data: retData });
  })
});

// Start the server
app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});