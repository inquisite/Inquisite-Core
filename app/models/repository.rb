class Repository
  include Neo4j::ActiveNode

  property :name, type: String, constraint: :unique
  property :readme, type: String
  property :web_site_url, type: String
  property :created_at, :type => DateTime
  property :updated_at, :type => DateTime

  has_one :both, :owner, model_class: User, type: 'owner'
  has_many :both, :collaborator, model_class: User, type: 'collaborator'
  has_many :both, :follower, model_class: User, type: 'follower'

  #
  # Return list of repositories for specified user
  #
  def self.get_repository_list_for_user(current_user)
    repositories_for_user = Neo4j::Session.query("match (u:User {email: {email}})--(repo:Repository) return repo order by repo.name", {:email => current_user.email}).to_a

    list = []
    repositories_for_user.each do |item|
      repository = {:uuid => item.repo.uuid, :readme_short => item.repo.readme.blank? ? '' : item.repo.readme.truncate(200)}
      item.repo.attributes.each { |key, value| repository[key] = value }
      list.push(repository)
    end

   return list
  end

  #
  # Create new repository and set specified user as owner
  #
  def self.add_repository_for_user(name, current_user, data)
    if(!current_user)
      raise("User must be defined")
    end
    if(!name)
      raise("Repository must be named")
    end

    # Throw exception if repository with this name already exists
    if(Repository.repository_name_exists?(name))
      raise ("Repository already exists with this name")
    end

    new_repo = Repository.new(name: name, readme: data[:readme], web_site_url: data[:web_site_url])
    new_repo.save

    Neo4j::Relationship.create('owner', new_repo, current_user)
    return new_repo
  end

  #
  # Delete repository. Must be owned by specified user
  #
  def self.delete_repository_for_user(repository_id, current_user)
    if(!current_user)
      raise("User must be defined")
    end
    if (!repository_id)
      raise("Repository ID must be defined")
    end

    if ((repo_to_reap=User.where(:email => current_user.email).owner(:r).where(:uuid => repository_id).all) && !repo_to_reap.blank?)
      begin
        repo_to_reap.destroy_all;
      rescue Exception => e
        raise("Could not delete repository: " + e.message)
      end

    else
      raise("Repository is not owned by you")
    end
    return nil
  end

  #
  # Check if repository exists with given name
  #
  def self.repository_name_exists?(name)
    repo_list = Repository.all.where(name: name)
    return (repo_list.length > 0) ? true : false
  end
end