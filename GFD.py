# GFD (Global Fault Detector) Pseudocode

membership = []
member_count = 0

# Allow GFD to always be listening -- LFD 1, LFD 2, LFD 3
# If GFD receives a message
    # If the message says "LFDx: add replica Sx"
        # member_count += 1
        # membership.append(Sx)
        # print “GFD: {membership_count} members: {membership}"
    # Else if the message says "delete replica Sx"    
        # If Sx is in membership:
            # member_count -= 1
            # remove Sx from membership
        # Else:
            # do nothing, this means LFD has connected to a server that hasn't registered



