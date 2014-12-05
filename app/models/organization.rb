class Organization 
  include Neo4j::ActiveNode

  property :name
  property :location
  property :email
  properly :web_site_url
  property :created_at, :type => DateTime
  property :updated_at, :type => DateTime

  has_many :both, :member, model_class: User, type: 'member'
  has_many :both, :repository, model_class: Repository, type: 'repository'

  validates :name, presence: true
end
