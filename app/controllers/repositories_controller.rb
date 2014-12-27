require 'repository.rb'
require 'data_type.rb'
require 'data_field.rb'

class RepositoriesController < ApplicationController

  # Require user to be authenticated
  #before_filter :authenticate

  #
  # List of repositories for user
  #
  def get_repository_list
    results = Repository.get_repository_list_for_user(current_user)
    render json:results;
  end

  ##
  # Add repository for current user
  #
  def add_repository
    @name = params[:name]

    result = {}

    begin
      # create new repository node
     repo = Repository.add_repository_for_user(@name, current_user, {:readme => params[:readme], :web_site_url => params[:websiteUrl]})
      result = {"status" => "OK", "uuid" => repo.uuid }
    rescue Exception => e
      result = {"status" => "ERR", "message" => e.message }
    end


    # TEST: set up a single data type
    #new_type = Neo4j::Node.create({_classname: 'DataType', name: 'Title', :data_type})
   # new_type = DataType.new( name:"Book", storage_type: "Graph")
    #new_type.save
    #new_field = DataField.new(name:"Title", data_type: "Text")
    #new_field.save
    #Neo4j::Relationship.create(:has, new_type, new_field)

    #@query = Neo4j::Session.query('MATCH (n:repository) WHERE n.name = "testmeown" RETURN n').to_a
    #@q = @query.pluck(":name");

    render json:result
  end

  #
  # Delete existing repository
  #
  def delete_repository
    @repository_id = params[:repository_id]

    begin
      # delete repository repository node
      repo = Repository.delete_repository_for_user(@repository_id, current_user)
      if (!(result = {"status" => "OK", }))
        result = {"status" => "ERR", "message" => "Failed" }
      end
    rescue Exception => e
      result = {"status" => "ERR", "message" => e.message }
    end
    render json:result
  end

  #
  # Check uniqueness of repository name
  #
  def check_name
    @name = params[:name]

    result = {:unique => false};
    begin
      result['unique'] = !(Repository.repository_name_exists?(@name))
    rescue Exception => e
      # noop
      result['error'] = e.message;
    end
    render json:result
  end

end