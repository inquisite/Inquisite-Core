class DataRelationshipType 
  include Neo4j::ActiveNode

  property :name_ltor
  property :name_rtol
  property :label
  property :description
  property :default, :type => Boolean
  property :created_at, :type => DateTime
  property :updated_at, :type => DateTime

  has_one :in, :left, model_class: DataType, type: 'left'
  has_one :in, :right, model_class: DataType, type: 'right'

  validates :name_ltor, presence: true
  validates :name_rtol, presence: true
  validates :label, presence: true

end