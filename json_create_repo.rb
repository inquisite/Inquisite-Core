require 'net/http'
require 'json'

uri = URI.parse('http://localhost:3000/repository/add/FOOOO')

begin
  Net::HTTP.start(uri.host, uri.port) do |http|
    req = Net::HTTP::Get.new(uri.path)
    req.basic_auth 'foo@bar.com', 'password'
    req['Accept'] = 'application/json'
    req['Content-Type'] = 'application/json'
    response = http.request(req)

    puts 'Request body:'
    puts response.body
    puts 'Headers:'
    response.header.each_header {|key,value| puts "#{key} = #{value}" }
  end
rescue StandardError => e
  raise StandardError, "Login failed. (Error was: #{e.to_s})"
end
