/**
 * Import function triggers from their respective submodules:
 *
 * const {onCall} = require("firebase-functions/v2/https");
 * const {onDocumentWritten} = require("firebase-functions/v2/firestore");
 *
 * See a full list of supported triggers at https://firebase.google.com/docs/functions
 */


const { onRequest } = require("firebase-functions/v2/https");
const { defineSecret } = require('firebase-functions/params');
const logger = require("firebase-functions/logger");
const linkedIn = require('linkedin-jobs-api');
const OpenAI = require("openai");
const cheerio = require('cheerio');
const z = require('zod')
const { zodResponseFormat } = require('openai/helpers/zod')

const apiKey = defineSecret('OPENAI_API_KEY');

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
  Company maturity (startup, scaleup, consolidated)
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

// Create and deploy your first functions
// https://firebase.google.com/docs/functions/get-started

exports.searchLI = onRequest({ cors: true }, (request, response) => {
  const queryOptions = request.body.data;

  linkedIn.query(queryOptions).then(data => {
    logger.info(data); // An array of Job objects
    let gptProms = [];
    let nonDupData = {}
    data.forEach(element => {
      const uniqueKey = element.company + element.position;
      if (!(uniqueKey in nonDupData)) {
        nonDupData[uniqueKey] = element;
      }
    })

    nonDupData = Object.values(nonDupData);
    const openai = new OpenAI({apiKey:apiKey.value()});

    nonDupData.forEach(element => {
      gptProms.push(fetch(element.jobUrl)
        .then((resp) => resp.text())
        .then((html) => {
          const $ = cheerio.load(html);
          const description = $('div.show-more-less-html__markup.show-more-less-html__markup--clamp-after-5.relative.overflow-hidden').first().html();
          const jsonContent = $('script[type="application/ld+json"]').first().html()
          //console.log('Extracted JSON:', jsonContent);
          let context = description
          if (jsonContent) {
            const jsonData = JSON.parse(jsonContent);
            if (jsonData.baseSalary)
              context += '\nbaseSalary:' + JSON.stringify(jsonData.baseSalary)
          }

          const completion = openai.chat.completions.create({
            model: "gpt-4o-mini",
            store: true,
            messages: [
              { "role": "user", "content": getCompanyPrompt(element.company, context) },
            ],
            response_format: zodResponseFormat(OutFormat, "offers")
          });

          completion.then((result) => {
            const msg = JSON.parse(result.choices[0].message.content)
            Object.assign(element, msg)
          });
          return completion
        }))
    });
    Promise.all(gptProms).then(() => {
      response.json({ data: nonDupData });
    })

  });
});
