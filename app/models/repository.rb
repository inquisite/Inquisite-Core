class Repository
  include Neo4j::ActiveNode
  property :name, type: String
  property :readme, type: String
  property :createOn, type: DateTime
  property :webSiteURL, type: String

  has_one :in, :Owner, model_class: User, type: 'owner'
  has_many :in, :Collaborator, model_class: User, type: 'collaborator'
  has_many :in, :Follower, model_class: User, type: 'follower'
end
