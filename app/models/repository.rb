class Repository
  include Neo4j::ActiveNode
  property :name, type: String
  property :readme, type: String
  property :web_site_url, type: String
  property :created_at, :type => DateTime
  property :updated_at, :type => DateTime

  has_one :in, :owner, model_class: User, type: 'owner'
  has_many :in, :collaborator, model_class: User, type: 'collaborator'
  has_many :in, :follower, model_class: User, type: 'follower'

  def self.add_repository_for_user(name, user)
    if(!user)
      raise("User must be defined")
    end
    if(!name)
      raise("Repository must be named")
    end

    # TODO: is repository name unique for this user?

    new_repo = Repository.new(name: name)
    new_repo.save

    Neo4j::Relationship.create('owner', new_repo, user)
    return new_repo
  end
end
