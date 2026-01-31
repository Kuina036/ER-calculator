import csv
import sys
import os
import glob

def normalize_name(name):
    """Normalize whitespace in names."""
    return ' '.join(name.split())

def load_round_data(file_path):
    """
    Reads a CSV file and returns a dictionary of team data for that round.
    Returns: { 'TeamName': {'total': float, 'kill': float} }
    """
    round_data = {}
    
    # Try different encodings
    encodings_to_try = ['utf-8-sig', 'cp949', 'utf-8']
    
    for encoding in encodings_to_try:
        try:
            with open(file_path, mode='r', encoding=encoding) as csvfile:
                reader = csv.DictReader(csvfile)
                if reader.fieldnames:
                    reader.fieldnames = [name.strip() for name in reader.fieldnames]

                # Check if the header looks correct
                # We expect at least 'teamName' or similar. 
                # If the encoding is wrong, the keys might be garbage.
                # However, strict checking is done below.
                
                rows = list(reader) # Read all to ensure encoding doesn't fail mid-file
                
                temp_data = {}
                valid_encoding = False
                
                for row in rows:
                    raw_name = row.get('teamName', '')
                    if not raw_name:
                        # Try to see if maybe the header was read wrong?
                        # But for now, just skip empty
                        continue
                        
                    valid_encoding = True # Found a teamName column at least
                    
                    team_name = normalize_name(raw_name)
                    if not team_name:
                        continue

                    try:
                        total = float(row.get('tournament total score', 0))
                        kill = float(row.get('tournament kill score', 0))
                    except ValueError:
                        continue

                    temp_data[team_name] = {'total': total, 'kill': kill}
                
                if valid_encoding:
                    round_data = temp_data
                    return round_data
                    
        except UnicodeDecodeError:
            continue
        except Exception as e:
            # If it's not an encoding error, it might be a file error
            print(f"Error reading {file_path} with {encoding}: {e}")
            continue

    if not round_data:
        print(f"Error: Could not read {file_path} with supported encodings or file is empty.")
        sys.exit(1)
        
    return round_data

def main():
    # Expand globs (wildcards) for Windows command line compatibility
    raw_args = sys.argv[1:]
    file_paths = []
    for arg in raw_args:
        expanded = glob.glob(arg)
        if expanded:
            file_paths.extend(expanded)
        else:
            # If it doesn't match a glob, assume it's a specific filename that might not exist yet or is just a name
            file_paths.append(arg)

    if not file_paths:
        print("사용법: 파일을 드래그하거나, 폴더에 .csv 파일이 있어야 합니다.")
        # Don't exit error immediately, just print message so pause works
        return

    # 1. Establish Base Teams from the first file
    base_file = file_paths[0]
    print(f"Reading base file (Round 1): {os.path.basename(base_file)}")
    base_data = load_round_data(base_file)
    
    valid_teams = set(base_data.keys())
    
    # Initialize cumulative scores
    tournament_stats = {}
    for team in valid_teams:
        tournament_stats[team] = {
            'team_name': team,
            'total_score': base_data[team]['total'],
            'kill_score': base_data[team]['kill']
        }

    # 2. Process subsequent files
    for file_path in file_paths[1:]:
        print(f"Processing: {os.path.basename(file_path)}")
        round_data = load_round_data(file_path)
        
        round_teams = set(round_data.keys())
        
        # Check for Mismatches
        # 1. Are there teams in this round that weren't in the base?
        new_unknown_teams = round_teams - valid_teams
        if new_unknown_teams:
            print(f"\n[ERROR] Team name mismatch in {os.path.basename(file_path)}!")
            print(f"Found unknown teams: {', '.join(new_unknown_teams)}")
            print("Aborting calculation to prevent data corruption.")
            sys.exit(1)
            
        # 2. Are there teams missing from this round? (Optional: Warning or Error?)
        # Usually strictly matching means the set must be identical.
        missing_teams = valid_teams - round_teams
        if missing_teams:
            print(f"\n[ERROR] Team list mismatch in {os.path.basename(file_path)}!")
            print(f"Missing teams: {', '.join(missing_teams)}")
            print("Aborting calculation.")
            sys.exit(1)

        # Accumulate Scores
        for team in valid_teams:
            tournament_stats[team]['total_score'] += round_data[team]['total']
            tournament_stats[team]['kill_score'] += round_data[team]['kill']

    # 3. Sort and Display Ranking
    ranked_teams = sorted(
        tournament_stats.values(),
        key=lambda x: (x['total_score'], x['kill_score']),
        reverse=True
    )

    print("\n" + "="*70)
    print(f"{'Rank':<5} {'Team Name':<30} {'Total Score':<15} {'Kill Score':<10}")
    print("="*70)

    current_rank = 1
    for team in ranked_teams:
        print(f"{current_rank:<5} {team['team_name']:<30} {team['total_score']:<15} {team['kill_score']:<10}")
        current_rank += 1
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
