require 'repository.rb'

class RepositoriesController < ApplicationController

  # Require user to be authenticated
  before_filter :authenticate_user!

  ##
  # Add repository for current user
  #
	def add
		@name = params[:name];
    @readme = params[:readme];
    @websiteURL = params[:websiteURL];


    #@repo = Repository.new(:name => @name, :createdOn => DateTime.now, :readme => @readme, :websiteURL => @websiteURL)
    #@repo.save

    # create new repository node
		newRepo = Neo4j::Node.create({_classname: "Repository", name: @name}, :repository)
    Neo4j::Relationship.create("owner", newRepo, current_user)
		
		#@query = Neo4j::Session.query('MATCH (n:repository) WHERE n.name = "testmeown" RETURN n').to_a
		#@q = @query.pluck(":name");

    render json:params
	end

end
