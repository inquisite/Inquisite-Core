class ApplicationController < ActionController::Base
  # Prevent CSRF attacks by raising an exception.
  # For APIs, you may want to use :null_session instead.
  protect_from_forgery with: :null_session

  def authenticate
    authenticate_or_request_with_http_basic do |email, password|
      puts email
      user = User.find_by(email: email)
      !user.nil? && user.valid_password?(password)
    end
    warden.custom_failure! if performed?
  end
end
