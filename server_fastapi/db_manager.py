import pymongo

class DBManager:
  def __init__(self):
    mongo = pymongo.MongoClient("mongodb://localhost:27017/")
    db = mongo["jobtoise"]
    self.collection = db["jobs"]
  
  def loadAll(self):
    return self.collection.find()

  def load(self, company, position):
    return self.collection.find_one({'company':company,'position':position})

  def save(self,jobList):
    self.collection.insert_many(jobList)

  def likeJob(self, company, position, like):
    self.collection.update_one({'company':company,'position':position}, {"$set": {"liked": like, "disliked":False}})

  def dislikeJob(self, company, position, dislike):
    self.collection.update_one({'company':company,'position':position}, {"$set": {"liked": False, "disliked": dislike}})