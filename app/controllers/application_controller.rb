class ApplicationController < ActionController::Base
  # Prevent CSRF attacks by raising an exception.
  # For APIs, you may want to use :null_session instead.
  protect_from_forgery with: :null_session

  def authenticate
    authenticate_or_request_with_http_basic do |email, password|
      @user = User.find_by(email: email)
      !@user.nil? && @user.valid_password?(password)
    end

    if performed?
      warden.custom_failure!
    else
      # sign in user. this makes sure Devise's current_user
      # function actually returns the user if used later
      sign_in(@user)
    end
  end
end
