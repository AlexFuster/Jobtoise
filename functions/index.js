/**
 * Import function triggers from their respective submodules:
 *
 * const {onCall} = require("firebase-functions/v2/https");
 * const {onDocumentWritten} = require("firebase-functions/v2/firestore");
 *
 * See a full list of supported triggers at https://firebase.google.com/docs/functions
 */

const { onRequest } = require("firebase-functions/v2/https");
const logger = require("firebase-functions/logger");
const linkedIn = require('linkedin-jobs-api');

// Create and deploy your first functions
// https://firebase.google.com/docs/functions/get-started

exports.searchLI = onRequest({cors: true}, (request, response) => {
  const queryOptions = request.body.data;

  linkedIn.query(queryOptions).then(data => {
    logger.info(data); // An array of Job objects
    response.json({data:data});
  });
});
