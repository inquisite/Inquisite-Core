require 'repository.rb'
require 'data_type.rb'
require 'data_field.rb'

class RepositoriesController < ApplicationController

  # Require user to be authenticated
  before_filter :authenticate

  ##
  # Add repository for current user
  #
  def add
    @name = params[:name]
    @readme = params[:readme]
    @websiteURL = params[:websiteURL]


    #@repo = Repository.new(:name => @name, :createdOn => DateTime.now, :readme => @readme, :websiteURL => @websiteURL)
    #@repo.save

    # create new repository node
    Repository.add_repository_for_user(@name, current_user)

    # TEST: set up a single data type
    #new_type = Neo4j::Node.create({_classname: 'DataType', name: 'Title', :data_type})
    new_type = DataType.new( name:"Book", storage_type: "Graph")
    new_type.save
    new_field = DataField.new(name:"Title", data_type: "Text")
    new_field.save
    Neo4j::Relationship.create(:has, new_type, new_field)

    #@query = Neo4j::Session.query('MATCH (n:repository) WHERE n.name = "testmeown" RETURN n').to_a
    #@q = @query.pluck(":name");

    render json:params
  end

end