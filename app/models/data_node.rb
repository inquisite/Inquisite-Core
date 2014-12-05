class DataNode 
  include Neo4j::ActiveNode

  property :created_at, :type => DateTime
  property :updated_at, :type => DateTime

  has_one :out, :owner, model_class: Repository, type: 'owner'
  has_one :out, :creator, model_class: User, type: 'creator'
  has_one :out, :type, model_class: DataType, type: 'is_a'


  def getType
    return "foo"
  end
end