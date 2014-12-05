class DataType 
  include Neo4j::ActiveNode

  property :name
  property :storage_type, :default => "Graph"
  property :description
  property :created_at, :type => DateTime
  property :updated_at, :type => DateTime

  has_many :out, :part_of, model_class: Repository, type: 'part_of'
  has_many :out, :has, model_class: DataField, type: 'has'

  validates :name, presence: true
  validates :storage_type, inclusion: { in: %w(Graph TableStore),
                                message: "%{value} is not a valid storage type" }

end