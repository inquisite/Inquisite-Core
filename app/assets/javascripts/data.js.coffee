# Place all the behaviors and hooks related to the matching controller here.
# All this logic will automatically be available in application.js.
# You can use CoffeeScript in this file: http://coffeescript.org/

inquisite = angular.module('inquisite',[
  'templates',
  'ngRoute',
  'ngAnimate',
  'ngResource'
])


inquisite.controller("DashboardController", [ '$scope', '$routeParams', '$location', '$resource',
  ($scope,$routeParams,$location,$resource)->
    $scope.pageClass = 'page-dashboard';
    #$scope.search = (keywords)->  $location.path("/").search('keywords',keywords)

    # Load repository list
    Repository = $resource('/repository/get_repository_list', { format: 'json' })
    Repository.query(user: 'seth', (results)-> $scope.repositories = results)

])

inquisite.controller("RepositoryController", [ '$scope', '$routeParams', '$location', '$resource',
  ($scope,$routeParams,$location,$resource)->
    $scope.pageClass = 'page-repository';

])

inquisite.controller("NewRepositoryController", [ '$scope', '$routeParams', '$location', '$resource',
  ($scope,$routeParams,$location,$resource)->
    # Set page class (for animation)
    $scope.pageClass = 'page-newRepository';

    # Handle cancel button (go back to dashboard)
    $scope.cancel = ->
      $location.path("/")

    # Is repository name unique?

    # Add new repository
    $scope.addNewRepository = ->
      if $scope.newRepositoryForm.$valid
        addRepository = $resource('/repository/add_repository', { format: 'json' })
        addRepository.get(name: $scope.repositoryName, readme: $scope.repositoryReadme, websiteUrl: $scope.repositoryWebsiteUrl,
          (results)->
            $scope.result = results
            if results['status'] == 'OK'
              $location.path("/")
            else
              alert(results['message'])
        )



])


inquisite.config([ '$routeProvider',
  ($routeProvider)->
    $routeProvider
    .when('/',
      templateUrl: "data/dashboard.html"
      controller: 'DashboardController'
    ).when('/dashboard',
      templateUrl: "data/dashboard.html"
      controller: 'DashboardController'
    )
    $routeProvider.when('/repository',
      templateUrl: "data/repository.html"
      controller: 'RepositoryController'
    )
    $routeProvider.when('/newRepository',
      templateUrl: "data/new_repository.html"
      controller: 'NewRepositoryController'
    )
])
