// Place all the behaviors and hooks related to the matching controller here.

inquisite = angular.module('inquisite',[
    'angularModalService',
  'templates',
  'ngRoute',
  'ngAnimate',
  'ngResource',
]);


inquisite.config([ '$routeProvider',
    function($routeProvider) {
        $routeProvider.when('/',
            {
                templateUrl: 'data/dashboard.html',
                controller: 'DashboardController'
            }
        ).when('/dashboard',
            {
                templateUrl: 'data/dashboard.html',
                controller: 'DashboardController'
            }
        ).when('/repository',
            {
                templateUrl: 'data/repository.html',
                controller: 'RepositoryController'
            }
        ).when('/newRepository',
            {
                templateUrl: 'data/new_repository.html',
                controller: 'NewRepositoryController'
            }
        ).when('/editor',
           {
                templateUrl: 'data/editor.html',
                controller: 'EditorController'
           }
    )  ;}
]);


inquisite.controller("DashboardController", [ '$scope', '$routeParams', '$location', '$resource', 'ModalService',
  function($scope,$routeParams,$location,$resource, ModalService) {
      $scope.pageClass = 'page-dashboard';

      // Load repository list
      $scope.getRepositoryList = function() {
         Repository = $resource('/repository/get_repository_list', {format: 'json'}, {'get' : {method: "GET", isArray: true}});
         Repository.get({}, function (results) {
             for(var i in results) {
                 if (!results.hasOwnProperty(i)) continue;

                 var t = moment( results[i]['created_at']);
                 results[i]['created_at_display'] = t.format("MM/DD/YYYY @ hh:mm a");
                 t = moment( results[i]['updated_at']);
                 results[i]['updated_at_display'] = t.format("MM/DD/YYYY @ hh:mm a");
             }
          $scope.repositories = results
        });
      };

      $scope.confirmDeleteRepository = function (repository) {
          ModalService.showModal({
              templateUrl: "delete_confirm.html",
              controller: "ConfirmDeleteRepositoryController",
              inputs: {
                  repository: repository
              }
          }).then(function(modal) {
              modal.element.modal();
              modal.close.then(function(result) {
                  if(result === 'DELETE') {
                      Repository = $resource('/repository/delete_repository/' + repository.uuid, {format: 'json'}, {'get' : {method: "GET", isArray: false}});
                      Repository.get({}, function (results) {
                          $scope.results = results;
                          $scope.getRepositoryList();

                      });
                  }
              });
          });

      };

      $scope.openEditor = function(repository) {
          $location.path("/editor");
      };

      // initial load of repository list for user
      $scope.getRepositoryList();
  }
]);

inquisite.controller("ConfirmDeleteRepositoryController", [ '$scope', 'repository', 'close',
    function($scope, repository, close) {

        $scope.repository = repository;
        $scope.close = function(result) {
            close(result, 500); // close, but give 500ms for bootstrap to animate
        };
    }
]);

inquisite.controller("RepositoryController", [ '$scope', '$routeParams', '$location', '$resource',
  function($scope,$routeParams,$location,$resource) {
      $scope.pageClass = 'page-repository';
  }
]);

inquisite.controller("NewRepositoryController", [ '$scope', '$routeParams', '$location', '$resource',
  function ($scope,$routeParams,$location,$resource) {
      // Set page class for animation
      $scope.pageClass = 'page-newRepository';

      //Handle cancel button(go back to dashboard )
      $scope.cancel = function () {
          $location.path("/");
      };


    // Is repository name unique?

    // Add new repository
    $scope.addNewRepository = function() {
        if ($scope.newRepositoryForm.$valid) {
            addRepository = $resource('/repository/add_repository', {format: 'json'}, {'get' : {method: "GET", isArray: false}});
            addRepository.get({name: $scope.repositoryName, readme: $scope.repositoryReadme, websiteUrl: $scope.repositoryWebsiteUrl},
            function(results) {
                $scope.result = results;
                if (results['status'] == 'OK') {
                    $location.path("/");
                } else {
                    alert(results['message']);
                }
            });
        }
    }
  }
]);

inquisite.controller("EditorController", [ '$scope', '$routeParams', '$location', '$resource',
    function($scope,$routeParams,$location,$resource) {
        $scope.pageClass = 'page-editor';
    }
]);

//
// Uniqueness lookup
//
//      Data service to perform uniqueness lookups
inquisite.factory('uniqueRepositoryNameDataService', ['$http', function ($http) {
    var serviceBase = '/repository/check_name/',
        dataFactory = {};

    dataFactory.checkUniqueValue = function (name) {
        if (!name) return true;
        return $http.get(serviceBase + '/' + escape(name)).then(
            function (results) {
                return results.data;
            });
    };

    return dataFactory;

}]);

//
//  Directive implementing uniqueness lookups
//
inquisite.directive('iqUnique', ['uniqueRepositoryNameDataService', function (uniqueRepositoryNameDataService) {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: function (scope, element, attrs, ngModel) {
            scope.nameChanged = function() {
                if (!ngModel || !element.val()) return;
                var currentValue = element.val();
                uniqueRepositoryNameDataService.checkUniqueValue(currentValue)
                    .then(function (d) {
                        //Ensure value that being checked hasn't changed
                        //since the Ajax call was made
                        if (currentValue == element.val()) {
                            ngModel.$setValidity('unique', d.unique);
                        }
                    }, function () {
                        //Probably want a more robust way to handle an error
                        //For this demo we'll set unique to true though
                        ngModel.$setValidity('unique', true);
                    });
            };
        }
    }
}]);