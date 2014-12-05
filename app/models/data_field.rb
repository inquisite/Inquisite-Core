class DataField 
  include Neo4j::ActiveNode


  property :name
  property :data_type
  property :description

  property :created_at, :type => DateTime
  property :updated_at, :type => DateTime


  validates :name, presence: true
  validates :data_type, inclusion: { in: %w(Text Integer Float Boolean Media Binary DateRange GeoReference List Currency Length Weight Time Calculation),
                                        message: "%{value} is not a valid data type" }

  # TODO: call this when data_type is set to establish settings fields for newly set data type
  def add_setting_fields_for_data_type(data_type)

  end
end
