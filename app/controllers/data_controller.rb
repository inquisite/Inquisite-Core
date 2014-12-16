class DataController < ApplicationController
  before_filter :authenticate_user!

  def index
    # Dashboard

  end
end
