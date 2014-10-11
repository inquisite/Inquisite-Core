require 'net/http'
require 'json'

auth_data = {
    user: {
        email: 'foo@bar.com',
        password: 'password',
    },
}

uri = URI.parse('http://localhost:3000/users/sign_in.json')

begin
  Net::HTTP.start(uri.host, uri.port) do |http|
    req = Net::HTTP::Post.new(uri.path)
    req.body = JSON.generate(auth_data)
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
